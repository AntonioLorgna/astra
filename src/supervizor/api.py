import os
from pathlib import Path
import time
from typing import List
from fastapi import FastAPI, File, HTTPException, status, UploadFile, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from pydantic import UUID4
from .. import celery_worker
from uuid import uuid4
from celery.result import AsyncResult
from .. import db
from .. import models
from sqlmodel import Session, delete, select
from .. import whisper_static
from .. import utils
import json
from logging import getLogger
logger = getLogger(__name__)
MEDIA_DIR = Path(os.environ.get("MEDIA_DIR"))

app = FastAPI()

@app.get("/")
def root_redirect():
    return RedirectResponse("/docs")


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