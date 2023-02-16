from dotenv import load_dotenv
import os, requests, logging
from celery.app import defaults as celery_defaults
from sys import stdout
from astra import utils
from astra.static.whisper_models import WhisperModels
from astra.worker.whisper import Whisper
from kombu import Queue
from pathlib import Path

load_dotenv("worker.env")
os.environ["WORKER"] = "Yes"


if os.environ.get("DEV_PORT") is not None:
    port = int(os.environ.get("DEV_PORT"))
    import debugpy

    debugpy.listen(("0.0.0.0", port))

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
logFormatter = logging.Formatter(celery_defaults.DEFAULT_TASK_LOG_FMT)
consoleHandler = logging.StreamHandler(stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

devices = utils.get_devices()
models_devices = utils.match_device_models(devices, WhisperModels.list_models())

whisper_instance = Whisper(devices, limit_loaded_models=1)
whisper_instance.download_avaliable_models()


MEDIA_DIR = Path(os.environ.get("MEDIA_DIR"))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

import astra.celery as celery

app = celery.app
app.conf.task_queues = tuple(Queue(name) for name in whisper_instance.avaliable_models)


def transcribe(task_id: str, model: str, filehash: str, file_webhook: str):
    filepath = MEDIA_DIR / str(filehash)

    if not filepath.is_file():
        with requests.get(file_webhook, timeout=5000) as r:
            if r.status_code == 200:
                r.raw.decode_content = True
                r_bytes = r.content
                r_filehash = utils.hash(r_bytes)
                if filehash != r_filehash:
                    raise Exception(
                        f"Файл повреждён, хэш не совпадает ({r_filehash}!={filehash})"
                    )
                filepath.write_bytes(r_bytes)
                r_bytes = None
            else:
                raise Exception("Не удаётся скачать файл")

    res = whisper_instance.transcribe(
        file=filepath, model_name=model, datetime_base=None
    )

    if os.environ.get("DEV") is None:
        filepath.unlink(True)

    return res.dict()


celery.worker_transcribe_func = transcribe
