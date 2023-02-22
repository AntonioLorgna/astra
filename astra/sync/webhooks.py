from logging import getLogger
from astra.core import models
from astra.core import schema
import requests

from astra.core.schema import TaskInfo
from astra.misc.utils import logging_setup

logger = getLogger(__name__)
logging_setup(logger)

headers = {"accept": "application/json", "Content-Type": "application/json"}
cookies = None

def task_status(job: models.Job, status: str, result: str = None, ok: bool = True, timeout_sec: int = 5):
    if len(job.tasks) == 0: 
        logger.warn(
            f"The job '{job.id}' has no tasks to notify."
        )
        return

    logger.info(
        f"Notify {len(job.tasks)} tasks of job '{job.id}'."
    )
    for task in job.tasks:
        try:
            data = TaskInfo(
                id=task.id,
                status=status,
                result=result,
                ok=ok
            )
            res = requests.post(
                url=task.status_webhook,
                headers=headers,
                cookies=cookies,
                data=data.json(),
                timeout=timeout_sec,
            )
            logger.info(
                f"Notify task '{task.id}' of job '{job.id}' with data: '{data.json(ensure_ascii=False)}'"
            )

            if res.ok:
                continue
                
            logger.warn(
                f"The job '{job.id}' updated successfully, \
    but result was not sent due to an error. (code {res.status_code})"
            )
        except Exception as e:
            logger.warn(
                f"The job '{job.id}' updated successfully, \
    but result was not sent due to an error. ({e})"
            )
