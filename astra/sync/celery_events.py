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
import asyncio, inspect

logger = getLogger(__name__)


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
        job = session.get(models.Job, job_id)
        if job is None:
            raise Exception(f"Job has id, but not exist in DB! ({job_id})")

        job.status = set_status

        if set_status == task_states.STARTED:
            job.startedAt = datetime.now()

        if set_result is not None:
            job.endedAt = datetime.now()
            job.result = set_result
        session.commit()

        webhooks.task_status(job, status=set_status, result=set_result, ok=job.is_ok())

        logger.info(f"Job '{job_id}' now has status '{job.status}'")


def task_event_process_generate(status: str):
    def task_event_process(event):
        r = AsyncResult(id=event["uuid"])
        if not asyncio.iscoroutinefunction(_update_task):
            _update_task(event["uuid"], status, r.result if r.ready() else None)
            return

        loop = asyncio.get_event_loop()
        coro = _update_task(event["uuid"], status, r.result if r.ready() else None)
        loop.create_task(coro)

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
