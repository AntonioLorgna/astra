import io
from dotenv import load_dotenv
from os import environ

import numpy as np
from astra import noise_reduction
from astra.worker import config

load_dotenv("worker.env")
environ["WORKER"] = "Yes"

import logging
from astra.misc.utils import devport_init, logging_setup
from celery.app import defaults as celery_defaults

logger = logging.getLogger(__name__)


devport_init()
logging_setup(logger, formatter=celery_defaults.DEFAULT_TASK_LOG_FMT)

import requests
from astra.misc import utils
from astra.core.whisper_models import WhisperModels
from astra.worker.whisper import Whisper
from kombu import Queue
from pathlib import Path

devices = utils.get_devices()
models_devices = utils.match_device_models(devices, WhisperModels.list_models())

whisper_instance = Whisper(devices, limit_loaded_models=1)
whisper_instance.download_avaliable_models()
dtln_models = noise_reduction.load_onnx_models(
    (
        config.WHISPER_MODELS_DIR / "model_p1.onnx",
        config.WHISPER_MODELS_DIR / "model_p2.onnx",
    )
)


MEDIA_DIR = Path(environ.get("MEDIA_DIR"))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

import astra.core.celery as celery

app = celery.app
app.conf.task_queues = tuple(Queue(name) for name in whisper_instance.avaliable_models)


def transcribe(job_id: str, model: str, filehash: str, file_webhook: str) -> str:
    filepath = MEDIA_DIR / str(filehash)

    if not filepath.is_file():
        headers = {"accept": "*/*", "Content-Type": "application/json"}
        r = requests.get(
            file_webhook, timeout=5, json={"job_id": job_id}, headers=headers
        )
        if not r.ok:
            raise Exception(
                f"Не удаётся скачать файл! (code: {r.status_code} msg: {r.text} url: {file_webhook})"
            )

        r.raw.decode_content = True

        hash = utils.HashIO()
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(65536, False):
                hash.update(chunk)
                f.write(chunk)
        r_filehash = str(hash)

        if filehash != r_filehash:
            # filepath.unlink(True)
            raise Exception(
                f"Файл повреждён, хэш не совпадает ({r_filehash} != {filehash})"
            )
        
    audio, wait = noise_reduction.load_file(filepath)
    audio = noise_reduction.denoise_onnx(dtln_models[0], dtln_models[1], audio).astype(np.float32)
    wait()

    res = whisper_instance.transcribe(
        file=audio, model_name=model, datetime_base=None
    )

    if environ.get("DEV_PORT") is None:
        filepath.unlink(True)

    return res.json(sort_keys=True, indent=2, ensure_ascii=False)


celery.worker_transcribe_func = transcribe
