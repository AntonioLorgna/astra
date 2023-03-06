from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import UUID4
from sqlmodel import Session
from astra.core import celery, db
from astra.core.schema import TaskInfo, TaskInit, task_states
from astra.core import models
import logging

logger = logging.getLogger(__name__)
app = FastAPI()

class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return record.getMessage().find("/healthcheck") == -1
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

@app.get("/")
async def root_redirect():
    return RedirectResponse("/docs")

@app.get("/healthcheck")
async def heartbeat():
    return Response("OK")

@app.post("/task")
async def add_task(task_init: TaskInit):
    with Session(db.engine) as session:
        user = session.get(models.User, task_init.user_id)
        if user is None:
            raise HTTPException(404, "User not found!")

        account = session.get(models.ServiceAccount, task_init.account_id)
        if account is None:
            raise HTTPException(404, "ServiceAccount not found!")
        
        task, job = models.Task.get(session, task_init, task_init)
        is_new_job = False
        
        if not (task or job):
            task, job, is_new_job = models.Task.create(session, task_init, task_init)
            session.commit()

        if is_new_job:
            celery.transcribe.apply_async(
                args=(job.model, job.filehash, task.file_webhook),
                task_id=str(job.id),
                queue=job.model,
            )

        if job.is_ended():
            return TaskInfo(
                id=task.id,
                status=job.status,
                result=job.result,
                ok=job.status == task_states.SUCCESS,
            )
        return TaskInfo(id=task.id, status=job.status)


@app.get("/task/{id}")
async def get_task(id: UUID4):
    with Session(db.engine) as session:
        task = session.get(models.Task, id)
        if task is None:
            return HTTPException(404, "Task not found!")
        job = task.job

        return TaskInfo(
            id=task.id, status=job.status, result=job.result, ok=job.is_ok()
        )


@app.on_event("startup")
async def startup():
    db.create_db_and_tables()


@app.post("/test")
async def debug_endpoint(request: Request):
    logger.warn("Body:")
    logger.warn(await request.json())
    return HTTPException(422)
