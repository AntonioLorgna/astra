import asyncio
from sys import stdout
import time
from typing import List
from fastapi import FastAPI, File, HTTPException, status, UploadFile, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from pydantic import UUID4
from .schema import TestTaskArgs
from . import celery_worker
from pathlib import Path
import os
from uuid import uuid4
from datetime import datetime
from celery.result import AsyncResult
from . import db
from . import models
from sqlmodel import Session, delete, select
from . import whisper_static
from . import utils
import logging
import json

if os.environ.get('DEV', False):
    import debugpy
    debugpy.listen(('0.0.0.0', 7999))
    # debugpy.wait_for_client()

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO) # set logger level
logFormatter = logging.Formatter\
("%(levelname)-8s: %(message)s")

consoleHandler = logging.StreamHandler(stdout) #set streamhandler to stdout
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

logger.info('Loading...')
MEDIA_DIR = Path(os.environ.get("MEDIA_DIR"))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

@app.get("/")
def root_redirect():
    return RedirectResponse("/docs")

@app.post("/test_task")
def run_test_task(args: TestTaskArgs):
    
    task = celery_worker.test_task.delay(args.a, args.b, args.c)
    return JSONResponse(task.get())


@app.put("/task",
    status_code=status.HTTP_202_ACCEPTED)
def add_task(
    model: whisper_static.WhisperModelsNames, 
    upload_file: UploadFile = File(format=[".mp3",".ogg",".flac"])):
    
    file_ext = upload_file.filename.split('.')[-1]
    file_bytes = upload_file.file.read()
    filehash = utils.filehash(file_bytes)

    # Validate if same file already processed
    with Session(db.engine) as session:
        expression = select(models.Task).where(
            models.Task.filehash==filehash,
            models.Task.status.in_([
                models.TaskStatus.PENDING, 
                models.TaskStatus.SENT, 
                models.TaskStatus.RECEIVED, 
                models.TaskStatus.STARTED,
                models.TaskStatus.RETRY,
                models.TaskStatus.SUCCESS
                ])
        )
        exist_tasks: List[models.Task] = session.exec(expression).all()

        db_task: models.Task = None
        # Check if larger model transcribed already
        for exist_task in exist_tasks:
            if exist_task.status == models.TaskStatus.SUCCESS:
                exist_task_model_params = whisper_static.WhisperModels[exist_task.model].value.parameters
                need_model_params = whisper_static.WhisperModels[model].value.parameters
                if need_model_params <= exist_task_model_params:
                    db_task = exist_task
                    break

        # Check if same model in transcribtion process
        if db_task is None:
            for exist_task in exist_tasks:
                if exist_task.model == model:
                    db_task = exist_task
                    break

        if db_task is not None:
            session.add(db_task)
            db_task.reruns += 1
            session.commit()
            
            return models.TaskSimpleInfo(   
                id=db_task.id,
                status=db_task.status
            )
                

        id = uuid4()

        
        filename = f"{int(time.time())}.{file_ext}"
        filepath = MEDIA_DIR/ filename
        
        if not filepath.is_file():
            filepath.write_bytes(file_bytes)

        db_task = models.Task(
            id=id,
            filehash=filehash,
            model=model,
            args={
                'model': model,
                'filehash': filehash,
                'filename': filename
            }
        )

        session.add(db_task)
        session.commit()

        celery_worker.test_transcribe.apply_async(
            args=(model, filehash, filename), 
            task_id=str(id),
            queue=model
        )
            
        return models.TaskSimpleInfo(   
            id=db_task.id,
            status=db_task.status
        )


@app.get("/files/{task_uuid}")
def get_file(task_uuid: UUID4):
    task: models.Task
    with Session(db.engine) as session:
        task = session.get(models.Task, task_uuid)
        if task is None or task.args.get('filename') is None:
            return HTTPException(404)
            
    filepath = MEDIA_DIR / task.args.get('filename')
    return FileResponse(filepath)


@app.get("/task/status/{id}")
def task_status(id: UUID4):
    task: models.Task
    with Session(db.engine) as session:
        task = session.get(models.Task, id)

        if task is None: 
            return HTTPException(404)

    res = AsyncResult(id=str(id), app=celery_worker.celery)
    if res.status != task.status:
        task.status
    return models.TaskSimpleInfo(   
        id=id,
        status=task.status
    )


@app.get("/task/{id}",
    response_model=models.Task)
def task_result(id: UUID4):
    task: models.Task
    with Session(db.engine) as session:
        task = session.get(models.Task, id)

        if task is None: 
            return HTTPException(404)

    res = AsyncResult(id=str(id), app=celery_worker.celery)
    if res.status != task.status:
        task.status

    return task


@app.delete("/task/{id}")
def task_abort(id: UUID4):
    task: models.Task
    with Session(db.engine) as session:
        task = session.get(models.Task, id)

        if task is None: 
            return HTTPException(404)
        

        if task.status in [models.TaskStatus.SUCCESS, models.TaskStatus.FAILURE]:
            return models.TaskSimpleInfo(
                id=id,
                status=task.status
            )

        res = AsyncResult(id=str(id), app=celery_worker.celery)
        res.revoke(terminate=True, wait=True)
        session.delete(task)
        session.commit()
        return models.TaskSimpleInfo(
            id=id,
            status=task.status
        )


@app.delete("/task")
def clear_tasks():
    with Session(db.engine) as session:
        statement = delete(models.Task)
        result = session.exec(statement)
        session.commit()
        return JSONResponse({'rowcount': result.rowcount})





@app.get("/task")
def select_tasks(
    status: models.TaskStatus | None = None,
    model: whisper_static.WhisperModelsNames | None = None,
    filehash: int | None = None
    ):
    with Session(db.engine) as session:
        expression = select(models.Task)
        if status is not None:
            expression = expression.where(models.Task.status == status)
        if model is not None:
            expression = expression.where(models.Task.model == model)
        if filehash is not None:
            expression = expression.where(models.Task.filehash == filehash)

        tasks: List[models.Task] = session.exec(expression).all()

        return tasks




@app.get("/stats",response_class=JSONResponse)
def celery_stats():
    stats = celery_worker.celery.control.inspect().stats()
    return json.loads(json.dumps(stats, default=str))


@app.on_event("startup")
def on_startup():
    db.create_db_and_tables()
    fire_and_forget(celery_db_syncronization())

def build_filename(filehash: int, file_ext:str):
    return f"{filehash}.{file_ext}"

def fire_and_forget(coro):
    import threading
    _loop = asyncio.new_event_loop()
    threading.Thread(target=_loop.run_forever, daemon=True).start()
    _loop.call_soon_threadsafe(asyncio.create_task, coro)

async def celery_db_syncronization():
    logger.info(f"Task events listening...")
    state = celery_worker.celery.events.State()

    def task_sent(event):
        # task = AsyncResult(id=event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.SENT
            logger.info(f"Task '{event['uuid']}' now has status '{db_task.status}'")
            session.commit()

    def task_received(event):
        # task = AsyncResult(id=event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.RECEIVED
            logger.info(f"Task '{event['uuid']}' now has status '{db_task.status}'")
            session.commit()

    def task_started(event):
        # task = state.tasks.get(event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.STARTED
            db_task.startedAt = datetime.now()
            logger.info(f"Task '{event['uuid']}' now has status '{db_task.status}'")
            session.commit()

    def task_succeeded(event):
        task = AsyncResult(id=event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.SUCCESS
            db_task.endedAt = datetime.now()
            db_task.result = task.result
            if os.environ.get("REMOVE_FILES_ON_SUCCESS") is not None:
                if db_task.args.get('filename') is None:
                    raise Exception("Task argument 'filename' is None!")
                filepath = MEDIA_DIR / str(db_task.args.get('filename'))
                filepath.unlink(missing_ok=True)
            logger.info(f"Task '{event['uuid']}' now has status '{db_task.status}'")
            session.commit()

    def task_failed(event):
        task = AsyncResult(id=event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.FAILURE
            db_task.endedAt = datetime.now()
            if isinstance(task.result, dict):
                db_task.result = task.result
            else:
                db_task.result = str(task.result)
            logger.info(f"Task '{event['uuid']}' now has status '{db_task.status}'")
            session.commit()

    def task_rejected(event):
        task = AsyncResult(id=event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.REJECTED
            db_task.endedAt = datetime.now()
            db_task.result = task.result
            logger.info(f"Task '{event['uuid']}' now has status '{db_task.status}'")
            session.commit()

    def task_retried(event):
        task = AsyncResult(id=event['uuid'])
        with Session(db.engine) as session:
            db_task = session.get(models.Task, event['uuid'])
            if db_task is None:
                raise Exception(f"Task has id, but not exist in DB! ({event['uuid']})")
            db_task.status = models.TaskStatus.RETRY
            db_task.endedAt = datetime.now()
            db_task.result = task.result
            logger.info(f"Task '{event['uuid']}' now has status '{db_task.status}'")
            session.commit()
            
    with celery_worker.celery.connection() as connection:
        recv = celery_worker.celery.events.Receiver(connection, handlers={
            'task-sent': task_sent,
            'task-received': task_received,
            'task-started': task_started,
            'task-succeeded': task_succeeded,
            'task-failed': task_failed,
            'task-rejected': task_rejected,
            'task-retried': task_retried,
        })

        recv.capture(limit=None, timeout=None, wakeup=True)
