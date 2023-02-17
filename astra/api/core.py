import requests
from astra import models
from astra.db import engine
from sqlmodel import Session, delete, select


def find_user(tg_id: str):
    with Session(engine) as session:
        e = select(models.User, where)