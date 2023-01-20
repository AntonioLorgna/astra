from celery import Celery
from dotenv import load_dotenv
import os, time, requests
from pathlib import Path
from zlib import crc32
from datetime import datetime


IS_WORKER = not bool(os.environ.get("IS_CELERY_APP", False))
if IS_WORKER:
    load_dotenv("worker.env")

MEDIA_DIR = Path(os.environ.get("WORKER_MEDIA_DIR", None if IS_WORKER else "./" ))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
FILES_ENDPOINT = os.environ.get("FILES_ENDPOINT")


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")
celery.conf.task_track_started = True
celery.conf.task_store_errors_even_if_ignored = True

if IS_WORKER:
    from .whisper import Whisper

    Whisper.download_avaliable_models()

if not IS_WORKER and False:
    from . import db
    from . import models
    from sqlmodel import Session

    state = celery.events.State()

    def task_sent(event):
        # task = state.tasks.get(event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.SENT
            session.commit()

    def task_received(event):
        # task = state.tasks.get(event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.RECEIVED
            session.commit()

    def task_started(event):
        # task = state.tasks.get(event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.STARTED
            db_task.startedAt = datetime.now()
            session.commit()

    def task_succeeded(event):
        task = state.tasks.get(event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.SUCCESS
            db_task.endedAt = datetime.now()
            db_task.result = task.result
            session.commit()

    def task_failed(event):
        task = state.tasks.get(event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.FAILURE
            db_task.endedAt = datetime.now()
            db_task.result = task.result
            session.commit()

    def task_rejected(event):
        task = state.tasks.get(event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.REJECTED
            db_task.endedAt = datetime.now()
            db_task.result = task.result
            session.commit()

    def task_retried(event):
        task = state.tasks.get(event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.RETRY
            db_task.endedAt = datetime.now()
            db_task.result = task.result
            session.commit()
            
    with celery.connection() as connection:
        recv = celery.events.Receiver(connection, handlers={
            'task-sent': task_sent,
            'task-received': task_received,
            'task-started': task_started,
            'task-succeeded': task_succeeded,
            'task-failed': task_failed,
            'task-rejected': task_rejected,
            'task-retried': task_retried,
        })
        recv.capture(limit=None, timeout=None, wakeup=True)




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

    res = Whisper.transcribe(filepath, model)

    return {
        'id': str(task_id),
        'model': model,
        'filehash': filehash,
        'text': res.get('text')
    }


