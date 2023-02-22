import asyncio
from pathlib import Path
from typing import List
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import UUID4, HttpUrl, Field
from uuid import uuid4
from sqlmodel import Session, select
from astra.core import celery
from astra.schema import TaskInfo, task_states
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


@app.post("/task")
async def add_task(task_init: models.TaskInit):
    with Session(db.engine) as session:
        user = session.get(models.User, task_init.user_id)
        if user is None:
            raise HTTPException(404, "User not found!")

        account = session.get(models.ServiceAccount, task_init.account_id)
        if account is None:
            raise HTTPException(404, "ServiceAccount not found!")

        expression = select(models.Job).where(
            models.Job.filehash == task_init.filehash, # same hash
            models.Job.model_quality >= WhisperModels.get_params(task_init.model) # better or like target model
        )
        exist_jobs = session.exec(expression).all()
        # Sorting by desc model quality
        exist_jobs = sorted(exist_jobs, key=lambda j: j.model_quality, reverse=True)

        inqueue_jobs = [j for j in exist_jobs if not j.startedAt]
        inprocess_jobs = [j for j in exist_jobs if j.startedAt and not j.endedAt]
        ready_jobs = [j for j in exist_jobs if j.endedAt]

        # Job at the lowest position in the queue
        best_inqueue_job = min(inqueue_jobs, key=lambda j: j.createdAt, default=None)
        # Job whith better model quality
        best_inprocess_job = max(inprocess_jobs, key=lambda j: j.model_quality, default=None)
        # Job whith better model quality
        best_ready_job = max(ready_jobs, key=lambda j: j.model_quality, default=None)

        target_job = None
        if best_ready_job: 
            target_job = best_ready_job
        elif best_inprocess_job: 
            target_job = best_inprocess_job
        elif best_inqueue_job: 
            target_job = best_inqueue_job
        target_job_exist = target_job is not None

        db_task = models.Task(**task_init.dict())

        if os.environ.get('DEV_PORT') and target_job and False:
            session.begin_nested()
            session.execute('LOCK TABLE "task" IN ACCESS EXCLUSIVE MODE;')
            for task in target_job.tasks:
                session.delete(task)
            session.commit()
            session.commit()

            session.begin_nested()
            session.execute('LOCK TABLE "job" IN ACCESS EXCLUSIVE MODE;')
            session.delete(target_job)
            session.commit()
            session.commit()
            target_job_exist = False
            target_job = None
        
        
        if not target_job:
            target_job = models.Job(
                filehash=task_init.filehash,
                model=task_init.model,
                model_quality=WhisperModels.get_params(task_init.model)
            )

            session.add(target_job)
        
        db_task.job = target_job
        session.add(db_task)
        session.commit()

        if not target_job_exist:
            celery.transcribe.apply_async(
                args=(task_init.model, task_init.filehash, task_init.file_webhook),
                task_id=str(target_job.id),
                queue=task_init.model,
            )

        if target_job.endedAt:
            return TaskInfo(
                id=db_task.id,
                status=target_job.status,
                result=target_job.result,
                ok=target_job.status == task_states.SUCCESS
            )
        return TaskInfo(
            id=db_task.id,
            status=target_job.status
        )


@app.get("/task/{id}")
async def get_task(id: UUID4):
    with Session(db.engine) as session:
        task = session.get(models.Task, id)
        if task is None:
            return HTTPException(404, "Task not found!")
        job = task.job
        
        return TaskInfo(
            id=task.id,
            status=job.status,
            result=job.result if job.endedAt else None,
            ok=job.status == task_states.SUCCESS if job.endedAt else None,
        )


@app.on_event("startup")
async def startup():
    pass


@app.post("/test")
async def debug_endpoint(request: Request):
    logger.warn("Body:")
    logger.warn(await request.json())
    return HTTPException(422)
