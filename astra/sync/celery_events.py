from datetime import datetime
from celery import Celery
from celery.events.receiver import EventReceiver
from celery.result import AsyncResult
from astra import db
from astra import models
from astra.schema import task_states
from astra.sync import webhooks
from sqlmodel import Session
from logging import getLogger
import asyncio, inspect

logger = getLogger(__name__)

class AsyncReceiver(EventReceiver):
    def process(self, type, event):
        """Process event by dispatching to configured handler."""
        handler = self.handlers.get(type) or self.handlers.get('*')
        if not handler: return
        if not inspect.iscoroutinefunction(handler):
            handler(event)
            return
            
        loop = asyncio.get_event_loop()
        loop.create_task(handler(event))
        


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

def task_event_process(event):
    r = AsyncResult(id=event["uuid"])

    loop = asyncio.get_event_loop()
    coro = None
    if r.ready():
        coro = _update_task(event["uuid"], r.state, r.result)
    else:
        coro = _update_task(event["uuid"], r.state)
    loop.create_task(coro)


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
                    "task-sent": task_event_process,
                    "task-received": task_event_process,
                    "task-started": task_event_process,
                    "task-succeeded": task_event_process,
                    "task-failed": task_event_process,
                    "task-rejected": task_event_process,
                    "task-retried": task_event_process,
                },
            )

            recv.capture(limit=None, timeout=None, wakeup=True)

