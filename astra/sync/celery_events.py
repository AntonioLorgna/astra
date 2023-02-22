from datetime import datetime
from celery import Celery
from celery.events.receiver import EventReceiver
from celery.result import AsyncResult
from astra.core import db
from astra.core import models
from astra.core import schema
from astra.core.schema import task_states
from astra.sync import webhooks
from sqlmodel import Session
from logging import getLogger
from astra.misc.utils import logging_setup
import asyncio, inspect

logger = getLogger(__name__)
logging_setup(logger)

class AsyncReceiver(EventReceiver):
    def process(self, type, event):
        """Process event by dispatching to configured handler."""
        handler = self.handlers.get(type) or self.handlers.get("*")
        if not handler:
            return
        if not inspect.iscoroutinefunction(handler):
            handler(event)
            return

        loop = asyncio.get_event_loop()
        loop.create_task(handler(event))


def _update_task(job_id: str, set_status: str, set_result=None):
    with Session(db.engine) as session:
        db_job = session.get(models.Job, job_id)
        if db_job is None:
            logger.error(f"Job has id, but not exist in DB! ({job_id})")
            return
            # raise Exception(f"Task has id, but not exist in DB! ({uuid})")

        session.begin_nested()
        session.execute('LOCK TABLE "job" IN ACCESS EXCLUSIVE MODE;')
        db_job.status = set_status

        if set_status == task_states.STARTED:
            db_job.startedAt = datetime.now()

        if set_result is not None:
            db_job.endedAt = datetime.now()
            db_job.result = set_result
        session.commit()
        session.commit()

        webhooks.task_status(
            db_job, 
            status=set_status, 
            result=set_result, 
            ok=db_job.status == schema.task_states.SUCCESS if db_job.endedAt else True)

        logger.info(f"Job '{job_id}' now has status '{db_job.status}'")


def task_event_process_generate(status: str):
    def task_event_process(event):
        r = AsyncResult(id=event["uuid"])
        loop = asyncio.get_event_loop()
        coro = None
        if r.ready():
            coro = _update_task(event["uuid"], status, r.result)
        else:
            coro = _update_task(event["uuid"], status)
        # loop.create_task(coro)

    return task_event_process


class CeleryTaskSync:
    def __init__(self, celery_app: Celery) -> None:
        self.app = celery_app

    def capture(self):
        logger.info(f"Task events listening...")
        # state = celery_app.events.State()

        with self.app.connection() as connection:
            recv = self.app.events.Receiver(
                connection,
                handlers={
                    "task-sent": task_event_process_generate(task_states.PENDING),
                    "task-received": task_event_process_generate(task_states.RECEIVED),
                    "task-started": task_event_process_generate(task_states.STARTED),
                    "task-succeeded": task_event_process_generate(task_states.SUCCESS),
                    "task-failed": task_event_process_generate(task_states.FAILURE),
                    "task-rejected": task_event_process_generate(task_states.REJECTED),
                    "task-retried": task_event_process_generate(task_states.RETRY),
                },
            )

            recv.capture(limit=None, timeout=None, wakeup=True)
