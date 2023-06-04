import io
from dotenv import load_dotenv
from os import environ

import numpy as np
from astra.api.utils import get_filesuffix
from astra.core.schema import Segment, TranscribeResult
from astra.worker import config
from astra.noise_reduction import load_file, save_file, load_onnx_models, denoise_onnx 

load_dotenv("worker.env")
environ["WORKER"] = "Yes"

import logging
from astra.core.utils import HashIO, devport_init, logging_setup
from celery.app import defaults as celery_defaults

logger = logging.getLogger(__name__)

BUFFER_CHUNK_SIZE = 0xffff
devport_init()
logging_setup(logger, formatter=celery_defaults.DEFAULT_PROCESS_LOG_FMT, level=logging.DEBUG)

import requests
from astra.core import utils
from astra.core.whisper_models import WhisperModels
from astra.worker import config
# from astra.worker.whisper import Whisper
from faster_whisper import WhisperModel
from faster_whisper.transcribe import Segment as FWSegment
from kombu import Queue
from pathlib import Path
import requests
import orjson

devices = utils.get_devices()
models_devices = utils.match_device_models(devices, WhisperModels.list_models())


import astra.core.celery as celery

app = celery.app
app.conf.task_queues = tuple(Queue(name) for name in ['large'])


class RemoteWorker:
    def __init__(self) -> None:
        self.whisper_model = None
        self.dtln_models = None
        RemoteWorker.__precreate_filedirectories()

    def load_models(self):
        self.whisper_model = WhisperModel(
            str(config.WHISPER_CT2_MODEL_DIR), 
            device=config.WHISPER_DEVICE, 
            compute_type=config.WHISPER_COMPUTE_TYPE)
        self.dtln_models = load_onnx_models((
            config.DTLN_ONNX_MODEL_1_PATH, 
            config.DTLN_ONNX_MODEL_2_PATH))
        
    def unload_models(self):
        self.whisper_model = None
        self.dtln_models = None

    def is_loaded_models(self):
        return self.whisper_model is not None and self.dtln_models is not None
    
    def process_task(self, job_id: str, model: str, filehash: str, file_webhook: str):
        if not self.is_loaded_models():
            raise Exception("Models not in the memory!")
        src_file_url = file_webhook
        src_file_path = RemoteWorker.__get_src_filepath(job_id)
        dn_file_path = RemoteWorker.__get_denoised_filepath(job_id)
        res_file_path = RemoteWorker.__get_result_filepath(job_id)

        self._download_audio(job_id, src_file_url, src_file_path, filehash)
        self._denoise_audio(src_file_path, dn_file_path)
        t = self._transcribe_audio(dn_file_path, res_file_path, vebose_progess=True)


        # if environ.get("DEV_PORT") is None:
        #     src_file_path.unlink(True)
        #     dn_file_path.unlink(True)
        #     res_file_path.unlink(True)

        return t

        
    def _download_audio(self, job_id: str, src_url: str, dist_file: Path, file_sha256sum: str=None):
        logger.debug(f"Downloading audio from url '{src_url}'")

        # with self.aiohttp_session.get(src_url) as resp:
        #     if resp.ok:
        #         hashio = HashIO()
        #         file = dist_file
        #         f_writer = file.open('wb')
        #         async for chunk in resp.content.iter_chunked(BUFFER_CHUNK_SIZE):
        #             hashio.update(chunk)
        #             f_writer.write(chunk)
        #         f_writer.close()
        #         hash = str(hashio)
        #         if file_sha256sum is not None and file_sha256sum != hash:
        #             if not config.DEBUG:
        #                 file.unlink(True)
        #             raise Exception("Bad filehash")
        #         logger.debug(f"File sucessfully downloaded to '{dist_file}'")
        #         return file
        #     raise Exception("Bad connection")
        
        headers = {"accept": "*/*", "Content-Type": "application/json"}
        r = requests.get(
            src_url, timeout=5, json={"job_id": job_id}, headers=headers
        )
        if not r.ok:
            raise Exception(
                f"Не удаётся скачать файл! (code: {r.status_code} msg: {r.text} url: {src_url})"
            )

        r.raw.decode_content = True

        hash = utils.HashIO()
        with open(dist_file, "wb") as f:
            for chunk in r.iter_content(BUFFER_CHUNK_SIZE, False):
                hash.update(chunk)
                f.write(chunk)
        r_filehash = str(hash)

        if file_sha256sum != r_filehash:
            # filepath.unlink(True)
            raise Exception(
                f"Файл повреждён, хэш не совпадает ({r_filehash} != {file_sha256sum})"
            )
        logger.debug(f"File sucessfully downloaded to '{dist_file}'")

    def _denoise_audio(self, src_file: Path, dist_file: Path=None)-> np.ndarray:
        logger.debug(f"Denoising audio from file '{src_file}'")
        audio = load_file(src_file)
        audio = denoise_onnx(self.dtln_models[0], self.dtln_models[1], audio)
        if dist_file is not None:
            ok = save_file(dist_file, audio)
            logger.debug(f"File sucessfully denoised and saved to '{dist_file}'")
        else:
            logger.debug(f"File sucessfully denoised")
        return audio
    
    def _transcribe_audio(self, src_file: Path, dist_file: Path=None, vebose_progess=False)->TranscribeResult:
        logger.debug(f"Transcribind audio from file '{src_file}'")
        audio = load_file(src_file)
        segments, info = self.whisper_model.transcribe(audio, beam_size=1)
        
        def map_segment(fw_segment: FWSegment):
            if vebose_progess:
                percent = fw_segment.end / info.duration * 100
                logger.info(f"Transcribed {fw_segment.end:.2f}/{info.duration:.2f} sec ({percent:.1f}%)")
            return RemoteWorker.__flatten_segment(fw_segment)

        segments = [map_segment(seg) for seg in segments]
        transcribtion = TranscribeResult(
            segments=segments
        )

        if dist_file is not None:
            with dist_file.open('w', encoding='utf-8') as f:
                f.write(transcribtion.json(indent=2, ensure_ascii=False))
            logger.info(f"File sucessfully transcribed and result saved to '{dist_file}'")
        else:
            logger.info(f"File sucessfully transcribed")

        return transcribtion

    def __flatten_segment(segment: FWSegment)->Segment:
        return Segment(
            start=segment.start,
            end=segment.end,
            text=segment.text.strip()
        )
    
    def __get_src_fileurl(task_id: str):
        # return f"{config.REST_SERVER_SUPERVISOR_URL}/{task_id}"
        return task_id # Because base_url was set in aiohttp_session
        
    def __precreate_filedirectories():
        for sub_dir in ['src', 'denoised', 'result']:
            dir = config.MEDIA_DIR / sub_dir
            dir.mkdir(exist_ok=True)
    
    def __get_src_filepath(task_id: str):
        return config.MEDIA_DIR/f"src/{task_id}"
    def __get_denoised_filepath(task_id: str):
        return config.MEDIA_DIR/f"denoised/{task_id}.wav"
    def __get_result_filepath(task_id: str):
        return config.MEDIA_DIR/f"result/{task_id}.json"


rw = RemoteWorker()
rw.load_models()

def transcribe(job_id: str, model: str, filehash: str, file_webhook: str) -> str:
    global rw
    try:
        res = rw.process_task(job_id, model, filehash, file_webhook)
    except Exception as e:
        logger.exception(e)
        raise e
    return res.json(sort_keys=False, indent=2, ensure_ascii=False)


celery.worker_transcribe_func = transcribe