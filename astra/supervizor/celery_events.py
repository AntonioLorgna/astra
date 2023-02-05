from pathlib import Path
import os
from uuid import uuid4
from datetime import datetime
from celery.result import AsyncResult
import debugpy
from astra import db
from astra import models
from astra.supervizor import webhooks
from sqlmodel import Session, delete, select
import asyncio
from logging import getLogger

logger = getLogger(__name__)
MEDIA_DIR = Path(os.environ.get("MEDIA_DIR"))

def __get_task(session: Session, uuid: str, set_status: models.TaskStatus, set_result = None):
    db_task = session.get(models.Task, uuid)
    if db_task is None:
        raise Exception(f"Task has id, but not exist in DB! ({uuid})")
    db_task.status = set_status
    if set_result is not None:
        if isinstance(set_result, dict):
            db_task.result = set_result
        else:
            db_task.result = str(set_result)
        db_task.endedAt = datetime.now()

    logger.info(f"Task '{uuid}' now has status '{db_task.status}'")
    return db_task

def task_sent(event):
    # task = AsyncResult(id=event['uuid'])
    with Session(db.engine) as session:
        db_task = __get_task(session, event['uuid'], models.TaskStatus.SENT)
        session.commit()

def task_received(event):
    # task = AsyncResult(id=event['uuid'])
    with Session(db.engine) as session:
        db_task = __get_task(session, event['uuid'], models.TaskStatus.RECEIVED)
        session.commit()

def task_started(event):
    # task = state.tasks.get(event['uuid'])
    with Session(db.engine) as session:
        db_task = __get_task(session, event['uuid'], models.TaskStatus.STARTED)
        session.commit()

def task_succeeded(event):
    task = AsyncResult(id=event['uuid'])
    with Session(db.engine) as session:
        db_task = __get_task(session, event['uuid'], models.TaskStatus.SUCCESS, task.result)

        if os.environ.get("REMOVE_FILES_ON_SUCCESS") is not None:
            if db_task.args.get('filename') is None:
                raise Exception("Task argument 'filename' is None!")
            filepath = MEDIA_DIR / str(db_task.args.get('filename'))
            filepath.unlink(missing_ok=True)
        
        session.commit()
        debugpy.breakpoint()
        webhooks.task_done(db_task)
        

def task_failed(event):
    task = AsyncResult(id=event['uuid'])
    with Session(db.engine) as session:
        db_task = __get_task(session, event['uuid'], models.TaskStatus.FAILURE, task.result)
        session.commit()

def task_rejected(event):
    task = AsyncResult(id=event['uuid'])
    with Session(db.engine) as session:
        db_task = __get_task(session, event['uuid'], models.TaskStatus.REJECTED, task.result)
        session.commit()

def task_retried(event):
    task = AsyncResult(id=event['uuid'])
    with Session(db.engine) as session:
        db_task = __get_task(session, event['uuid'], models.TaskStatus.RETRY, task.result)
        session.commit()


async def celery_db_syncronization(celery_app):
    """Внимание! Эта функция полностью блокирует процесс.
    """
    logger.info(f"Task events listening...")
    # state = celery_app.events.State()

            
    with celery_app.connection() as connection:
        recv = celery_app.events.Receiver(connection, handlers={
            'task-sent': task_sent,
            'task-received': task_received,
            'task-started': task_started,
            'task-succeeded': task_succeeded,
            'task-failed': task_failed,
            'task-rejected': task_rejected,
            'task-retried': task_retried,
        })

        recv.capture(limit=None, timeout=None, wakeup=True)
