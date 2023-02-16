from logging import getLogger
from astra.models import Task as TaskModel
import requests

from astra.schema import TaskSimpleInfo

logger = getLogger(__name__)

headers = {"accept": "application/json", "Content-Type": "application/json"}
cookies = None

def task_status(task: TaskModel, timeout_sec: int = 5):
    if task.status_webhook is None: return

    try:
        data = TaskSimpleInfo(
            id=task.id,
            status=task.status,
            result=task.result.result if task.result_id else None,
            ok=task.result.ok if task.result_id else False
        )
        res = requests.post(
            url=task.status_webhook,
            headers=headers,
            cookies=cookies,
            json=data,
            timeout=timeout_sec,
        )

        if res.ok:
            return
            
        logger.warn(
            f"The task '{task.id}' updated successfully, \
but result was not sent due to an error. (code {res.status_code})"
        )
    except Exception as e:
        logger.warn(
            f"The task '{task.id}' updated successfully, \
but result was not sent due to an error. ({e})"
        )
