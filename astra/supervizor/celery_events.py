from pathlib import Path
import os
from datetime import datetime
from celery.result import AsyncResult
from astra import db
from astra import models
from astra.schema import task_states
from astra.supervizor import webhooks
from sqlmodel import Session
from logging import getLogger

logger = getLogger(__name__)
MEDIA_DIR = Path(os.environ.get("MEDIA_DIR"))


def _update_task(uuid: str, set_status: str, set_result=None):    
    with Session(db.engine) as session:
        db_task:models.Task = session.get(models.Task, uuid)
        if db_task is None:
            raise Exception(f"Task has id, but not exist in DB! ({uuid})")
        db_task.status = set_status
        if set_result is not None:
            result = models.Result(
                task=db_task, 
                result=set_result, 
                ok=(set_status==task_states.SUCCESS)
                )
            session.add(result)
            db_task.result = result
            db_task.endedAt = datetime.now()

        webhooks.task_status(db_task)

        logger.info(f"Task '{uuid}' now has status '{db_task.status}'")

        session.commit()


def task_sent(event):
    # task = AsyncResult(id=event['uuid'])
    _update_task(event["uuid"], task_states.PENDING)


def task_received(event):
    # task = AsyncResult(id=event['uuid'])
    _update_task(event["uuid"], task_states.RECEIVED)


def task_started(event):
    # task = state.tasks.get(event['uuid'])
    _update_task(event["uuid"], task_states.STARTED)


def task_succeeded(event):
    task = AsyncResult(id=event["uuid"])
    _update_task(event["uuid"], task_states.SUCCESS, task.result)


def task_failed(event):
    task = AsyncResult(id=event["uuid"])
    _update_task(event["uuid"], task_states.FAILURE, task.result)


def task_rejected(event):
    task = AsyncResult(id=event["uuid"])
    _update_task(event["uuid"], task_states.REJECTED, task.result)


def task_retried(event):
    task = AsyncResult(id=event["uuid"])
    _update_task(event["uuid"], task_states.RETRY, task.result)


async def celery_db_syncronization(celery_app):
    """Внимание! Эта функция полностью блокирует процесс."""
    logger.info(f"Task events listening...")
    # state = celery_app.events.State()

    with celery_app.connection() as connection:
        recv = celery_app.events.Receiver(
            connection,
            handlers={
                "task-sent": task_sent,
                "task-received": task_received,
                "task-started": task_started,
                "task-succeeded": task_succeeded,
                "task-failed": task_failed,
                "task-rejected": task_rejected,
                "task-retried": task_retried,
            },
        )

        recv.capture(limit=None, timeout=None, wakeup=True)
