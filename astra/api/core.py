import requests
from astra import models
from astra.db import engine
from sqlmodel import Session, delete, select
from logging import getLogger
from astra.api import config
logger = getLogger(__name__)

from astra.schema import TaskSimpleInfo


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

def get_user_tg(tg_id: str):
    with Session(engine) as session:
        statement = select(models.User, models.UserServiceAccount) \
            .where(models.User.id == models.UserServiceAccount.user_id,
                   models.UserServiceAccount.service_id == tg_id,
                   models.UserServiceAccount.service_name == 'telegram')
        t = session.exec(statement).first()
        if t is None: return None
        return t[0]

def add_user_tg(tg_id: str, role: int = 0, limit_seconds: int = 0):
    with Session(engine) as session:
        user = models.User(
            role=role, 
            limit_seconds=limit_seconds)
        
        account = models.UserServiceAccount(
            service_id=tg_id,
            service_name='telegram',
            user=user
        )

        session.add_all(user, account)
        session.commit()
        return user

def add_task(user: models.User, task_init: models.TaskInit):
    response = requests.put(
        config.SUPERVIZOR_ADDRESS + '/task',
        json={
            'user_id':user.id,
            **task_init.dict()
        })
    if response.ok:
        return TaskSimpleInfo(**response.json())
    
    logger.error(f"Can not add new task: '{response.content}' ({response.status_code})")
    return False

def get_task(id: str):
    with Session(engine) as session:
        statement = select(models.Task) \
            .where(models.Task.id == id)
        return session.exec(statement).first()
