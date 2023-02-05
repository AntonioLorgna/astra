from logging import getLogger

from astra.models import Task as TaskModel
logger = getLogger(__name__)
import requests


async def task_done(task: TaskModel, timeout_sec: int= 5):
    if task.webhook is None: 
        logger.warn(f"The task '{task.id}' completed successfully, but the webhook is missing.")
        return

    headers = {}
    cookies = {}
    data = {}
    res = requests.post(url=task.webhook, 
        headers=headers, 
        cookies=cookies,
        data=data,
        timeout=timeout_sec)

    if res.ok:
        logger.debug(f"The task '{task.id}' completed successfully, the result was sent.")
        return

    logger.warn(f"The task '{task.id}' completed successfully, \
the result was not sent due to an error. (code {res.status_code})")