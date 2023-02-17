from dotenv import load_dotenv
load_dotenv('api.env')
import os
from fastapi import FastAPI
import logging
from sqlmodel import Session, delete, select
from astra import utils
from astra import db
from astra import models
from astra.api.bot import dp, bot, get_wh_path, get_wh_endpoint
from aiogram import types, Dispatcher, Bot

logger = logging.getLogger(__name__)
utils.logging_setup(logger)



if os.environ.get('DEV', False):
    logger.warn("It's developement build!")
    import debugpy
    debugpy.listen(('0.0.0.0', 7000))



app = FastAPI()


@app.get('/api/test')
def test_helloworld():
    return 'Hello World!'


@app.on_event("startup")
async def on_startup():
    # DB
    db.create_db_and_tables()

    # TG
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != get_wh_endpoint():
        await bot.set_webhook(
            url=get_wh_endpoint()
        )
        logger.info(f"Using webhook url '{get_wh_endpoint()}' for telegram bot.")


@app.post(get_wh_path())
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.process_update(telegram_update)


@app.on_event("shutdown")
async def on_shutdown():
    # TG
    await bot.session.close()