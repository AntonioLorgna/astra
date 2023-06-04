import aiohttp, orjson
from astra.core import schema
from astra.api.utils import short_uuid
from logging import getLogger
from astra.api import config
from aiogram import Bot
import aiohttp.typedefs as aiohttp_typedefs

from astra.core.utils import result_stringify

logger = getLogger(__name__)

from astra.core.schema import TaskInfo, TaskInit

aiohttp_typedefs.DEFAULT_JSON_ENCODER = orjson.dumps
aiohttp_typedefs.DEFAULT_JSON_DECODER = orjson.loads


async def add_task(task_init: TaskInit):
    payload = task_init.json()
    headers = {"Content-type": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            config.SUPERVIZOR_URL + "/task", data=payload, headers=headers
        ) as response:
            if response.ok:
                return TaskInfo(**(await response.json()))

            logger.error(
                f"Can not add new task: '{await response.content.read()}' ({response.status})"
            )
    return None


async def result_exist(info: TaskInfo, bot: Bot, user_id: str):
    result = schema.TranscribeResult(**orjson.loads(info.result))
    await bot.send_message(
        user_id, f"#T{short_uuid(info.id)} Анализ данной записи уже был произведён."
    )
    await bot.send_message(user_id, result_stringify(result, " "))
