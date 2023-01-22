from sys import stdout
from celery import Celery
from celery.app import defaults as celery_defaults
from kombu import Queue
from dotenv import load_dotenv
import os, time, requests
from pathlib import Path
from zlib import crc32
from datetime import datetime
import logging
import src.utils as utils
from .whisper_models import WhisperModels, whisper_models_names
logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO) # set logger level
logFormatter = logging.Formatter\
(celery_defaults.DEFAULT_TASK_LOG_FMT)
consoleHandler = logging.StreamHandler(stdout) #set streamhandler to stdout
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

devices = []
IS_WORKER = not bool(os.environ.get("IS_CELERY_APP", False))
if IS_WORKER:
    from .whisper import Whisper
    if os.environ.get('DEV', False):
        import debugpy
        debugpy.listen(('0.0.0.0', 7998))
    devices = utils.get_devices()
    models_devices = utils.match_device_models(devices, [m.value for m in WhisperModels])

MEDIA_DIR = Path(os.environ.get("WORKER_MEDIA_DIR", None if IS_WORKER else "./" ))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
FILES_ENDPOINT = os.environ.get("FILES_ENDPOINT")


celery = Celery(devices[-1].name if devices else 'supervizor')
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")
celery.conf.task_track_started = True
celery.conf.task_store_errors_even_if_ignored = True
celery.conf.worker_concurrency = 1
celery.conf.worker_prefetch_multiplier = 1
celery.conf.worker_send_task_events = True

if IS_WORKER:
    
    w = Whisper(devices, limit_loaded_models=1)

    celery.conf.task_queues = tuple(
        Queue(name) for name in w.avaliable_models
    )
    
    w.download_avaliable_models()
else:
    celery.conf.task_queues = tuple(
        Queue(name) for name in whisper_models_names
    )


@celery.task(name="astra_test_task")
def test_task(a, b, c):
    time.sleep(a)
    return {
        'a': a,
        'b': b,
        'c': c,
        'result': c+b
    }


@celery.task(bind=True, name="test_transcribe")
def test_transcribe(self, model: str, filehash: int, filename: str):
    # time.sleep(0)
    task_id = self.request.id
    filepath = MEDIA_DIR / str(filename)

    if not filepath.is_file():
        with requests.get(FILES_ENDPOINT + "/" + task_id, timeout=5000) as r:
            if r.status_code == 200:
                r.raw.decode_content = True
                r_bytes = r.content
                r_filehash = crc32(r_bytes) ^ len(r_bytes)
                if filehash != r_filehash:
                    raise Exception(f"Файл повреждён ({r_filehash}!={filehash})")
                filepath.write_bytes(r_bytes)
                r_bytes = None
            else:
                raise Exception("Не удаётся скачать файл")

    res = w.transcribe(file=filepath, model_name=model, datetime_base=None)

    return {
        'id': str(task_id),
        'model': model,
        'filehash': filehash,
        'text': res.get('text')
    }


