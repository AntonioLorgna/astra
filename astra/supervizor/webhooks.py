from logging import getLogger
from astra.models import Task as TaskModel
import requests

logger = getLogger(__name__)


def task_done(task: TaskModel, timeout_sec: int = 5):
    if task.webhook is None:
        logger.warn(
            f"The task '{task.id}' completed successfully, but the webhook is missing."
        )
        return

    headers = {"accept": "application/json", "Content-Type": "application/json"}
    cookies = None
    try:
        res = requests.post(
            url=task.webhook,
            headers=headers,
            cookies=cookies,
            json=task.result,
            timeout=timeout_sec,
        )

        if res.ok:
            logger.info(
                f"The task '{task.id}' completed successfully, the result was sent."
            )
            return
        logger.warn(
            f"The task '{task.id}' completed successfully, \
but result was not sent due to an error. (code {res.status_code})"
        )
    except Exception as e:
        logger.warn(
            f"The task '{task.id}' completed successfully, \
but result was not sent due to an error. ({e})"
        )
