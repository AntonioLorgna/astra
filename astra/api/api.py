from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
load_dotenv('api.env')
import os
from fastapi import FastAPI
import logging
from sqlmodel import Session, delete, select
from astra import utils
from astra import db
from astra import models
from astra.api.bot import start_bot, stop_bot, get_wh_path, set_bot_webhook, process_wh_update
logger = logging.getLogger(__name__)
utils.logging_setup(logger)

utils.devport_init()

app = FastAPI()
start_bot()

@app.get('/api/test')
def test_helloworld():
    return 'Hello World!'


@app.on_event("startup")
async def on_startup():
    # DB
    db.create_db_and_tables()
    # TG

    await set_bot_webhook()


@app.post(get_wh_path())(process_wh_update)



@app.on_event("shutdown")
async def on_shutdown():
    # TG
    await stop_bot()