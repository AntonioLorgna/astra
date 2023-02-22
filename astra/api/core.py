from datetime import timedelta
import aiohttp, orjson
from astra.core import models
from astra.core import schema
from astra.api.utils import short_uuid
from astra.core.db import engine
from sqlmodel import Session, delete, select
from logging import getLogger
from astra.api import config
import aiohttp.typedefs as aiohttp_typedefs

from astra.misc.utils import result_stringify
logger = getLogger(__name__)

from astra.core.schema import TaskInfo
aiohttp_typedefs.DEFAULT_JSON_ENCODER = orjson.dumps
aiohttp_typedefs.DEFAULT_JSON_DECODER = orjson.loads

def get_user(id: str):
    with Session(engine) as session:
        statement = select(models.User) \
            .where(models.User.id == id)
        return session.exec(statement).first()

def add_user(role: int = 0, limit_seconds: int = 0):
    with Session(engine) as session:
        user = models.User(
            role=role, 
            limit_seconds=limit_seconds)
        
        session.add(user)
        session.commit()
        return user

def get_account(tg_id: str):
    with Session(engine) as session:
        statement = select(models.ServiceAccount) \
            .where(models.ServiceAccount.service_id == tg_id,
                   models.ServiceAccount.service_name == 'telegram')
        return session.exec(statement).first()

def get_user_tg(tg_id: str, session: Session):
    statement = select(models.User, models.ServiceAccount) \
        .where(models.User.id == models.ServiceAccount.user_id,
                models.ServiceAccount.service_id == tg_id,
                models.ServiceAccount.service_name == 'telegram')
    t = session.exec(statement).first()
    if t is None: return (None, None)
    return t

def add_user_tg(tg_id: str, session: Session, role: int = 0, limit_seconds: int = 0):
    session.begin_nested()
    session.execute('LOCK TABLE "user" IN ACCESS EXCLUSIVE MODE;')
    user = models.User(
        role=role, 
        limit_seconds=limit_seconds)
    
    session.add(user)
    session.commit()
    session.begin_nested()
    session.execute('LOCK TABLE "service_account" IN ACCESS EXCLUSIVE MODE;')
    account = models.ServiceAccount(
        service_id=tg_id,
        service_name='telegram',
        user=user
    )
    session.add(account)
    session.commit()
    session.commit()
    return (user, account)

async def add_task(task_init: models.TaskBase):
    payload = task_init.json()
    headers = {
        'Content-type': 'application/json'
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            config.SUPERVIZOR_ADDRESS + '/task',
            data=payload,
            headers=headers) as response:
            
            if response.ok:
                return TaskInfo(**(await response.json()))
            
            logger.error(f"Can not add new task: '{await response.content.read()}' ({response.status})")
    return None

def get_task(job_id: str, session: Session):
    return session.get(models.Task, id)


async def result_exist(info: TaskInfo, bot, user_id):
    result = schema.TranscribeResult(**orjson.loads(info.result))
    await bot.send_message(user_id, f"#T{short_uuid(info.id)} Анализ данной записи уже был произведён.")
    await bot.send_message(user_id, result_stringify(result, " "))