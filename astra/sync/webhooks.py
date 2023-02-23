from logging import getLogger
import requests

logger = getLogger(__name__)

from astra.core import models
from astra.core.schema import TaskInfo


headers = {"accept": "application/json", "Content-Type": "application/json"}
cookies = None


def task_status(
    job: models.Job,
    status: str,
    result: str = None,
    ok: bool = True,
    timeout_sec: int = 5,
):
    if len(job.tasks) == 0:
        logger.warn(f"The job '{job.id}' has no tasks to notify.")
        return

    logger.info(f"Notify {len(job.tasks)} tasks of job '{job.id}'.")
    for task in job.tasks:
        try:
            data = TaskInfo(id=task.id, status=status, result=result, ok=ok)
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

            logger.error(
                f"The job '{job.id}' updated successfully, \
    but result was not sent due to an error. (code {res.status_code})"
            )
        except Exception as e:
            logger.error(
                f"The job '{job.id}' updated successfully, \
    but result was not sent due to an error. ({e})"
            )
