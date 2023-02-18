import asyncio
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import UUID4, HttpUrl
from uuid import uuid4
from sqlmodel import Session, select
from astra.core import celery
from astra.schema import TaskSimpleInfo, task_states
from astra.static.whisper_models import WhisperModels
from astra import db, models
import os
from logging import getLogger
from astra.core.celery import app as celery_app

logger = getLogger(__name__)
app = FastAPI()

@app.get("/")
async def root_redirect():
    return RedirectResponse("/docs")


@app.put("/task")
async def add_task(
    user_id: str,
    task_init: models.TaskInit
):
    # Validate if same file already processed
    with Session(db.engine) as session:
        user = session.get(models.User, user_id)
        if user is None:
            raise HTTPException(404, "User not found!")

        expression = select(models.Task).where(
            models.Task.filehash == task_init.filehash,
            models.Task.status.in_(
                [
                    task_states.PENDING,
                    task_states.RECEIVED,
                    task_states.STARTED,
                    task_states.SUCCESS,
                ]
            ),
        )
        exist_tasks: List[models.Task] = session.exec(expression).all()

        db_task: models.Task = None
        # Check if better model or same transcribed already
        for exist_task in exist_tasks:
            if WhisperModels.is_more_accurate(task_init.model, exist_task.model, True):
                db_task = exist_task
                break

        if db_task is not None:
            if user not in db_task.users:
                db_task.users.append(user)

            db_task.reruns += 1
            session.add(user)
            session.add(db_task)
            session.commit()

            if db_task.result_id is not None:
                result = db_task.result
                return TaskSimpleInfo(
                    id=db_task.id, 
                    status=db_task.status, 
                    result=result.result if result else None, 
                    ok=result.ok if result else True
                    )
            
            return TaskSimpleInfo(
                id=db_task.id, 
                status=db_task.status
                )

        id = uuid4()

        db_task = models.Task(
            id=id,
            filehash=task_init.filehash,
            model=task_init.model,
            audio_duration=task_init.audio_duration,
            status_webhook=task_init.status_webhook,
            file_webhook=task_init.file_webhook
        )
        db_task.users.append(user)

        session.add(user)
        session.add(db_task)
        session.commit()

        celery.transcribe.apply_async(
            args=(
                task_init.model, 
                task_init.filehash, 
                task_init.file_webhook), 
            task_id=str(id), 
            queue=task_init.model
        )

        return TaskSimpleInfo(id=db_task.id, status=db_task.status)

@app.get("/task/{id}")
async def get_task(id: UUID4):
    with Session(db.engine) as session:
        task = session.get(models.Task, id)

        if task is None:
            return HTTPException(404, "Task not found!")
        
        return TaskSimpleInfo(
            id=task.id, 
            status=task.status,
            result=task.result.result if task.result_id else None,
            ok=task.result.ok if task.result_id else False
            )

@app.on_event('startup')
async def startup():
    pass