from celery import Celery
from dotenv import load_dotenv
import os, time, requests
from pathlib import Path
from zlib import crc32
from random import randint

load_dotenv(".env")

IS_WORKER = not bool(os.environ.get("IS_CELERY_APP", False))

MEDIA_DIR = Path(os.environ.get("WORKER_MEDIA_DIR", None if IS_WORKER else "./" ))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
FILES_ENDPOINT = os.environ.get("FILES_ENDPOINT")


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")



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
            else:
                raise Exception("Не удаётся скачать файл")


    # transcribe###
    raw = filepath.read_bytes()

    a, b = randint(0, 10), randint(0,10)
    return {
        'id': str(task_id),
        'model': model,
        'filehash': filehash,
        'filepath': str(filepath.resolve(True)),
        'filelen': len(raw),
        f"{a}+{b}": a+b
    }
