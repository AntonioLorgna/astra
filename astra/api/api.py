from datetime import timedelta
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

load_dotenv("api.env")
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
from sqlmodel import Session, delete, select
from astra import utils
from astra import db
from astra import models
from astra import schema
from astra.api import core
from astra.api import config
from astra.api.bot import (
    start_bot,
    stop_bot,
    get_bot_wh_path,
    set_bot_webhook,
    process_wh_update,
)
from astra.schema import task_states
from astra.utils import result_stringify
import json

logger = logging.getLogger(__name__)
utils.logging_setup(logger)

utils.devport_init()

app = FastAPI()
start_bot()


@app.get("/api/test")
def test_helloworld():
    return "Hello World!"


@app.on_event("startup")
async def on_startup():
    # DB
    db.create_db_and_tables()
    # TG
    await set_bot_webhook()


@app.on_event("shutdown")
async def on_shutdown():
    # TG
    await stop_bot()


@app.post(get_bot_wh_path())(process_wh_update)
@app.post("/status")
async def process_task_status(task_info: schema.TaskSimpleInfo):
    bot = Bot.get_current()

    with Session(db.engine) as session:
        task = session.get(models.Task, task_info.id)
        if task is None:
            raise Exception(
                f"Task with id '{task_info.id}' does not exist, but task_info contains it"
            )
        user_id = task.account.service_id

        if task_info.status != task_states.SUCCESS:
            bot.send_message(
                user_id, f"Ваша задача находится в статусе {task_info.status}"
            )
            return
        result = schema.TranscribeResult(**json.loads(task_info.result))
        execution_time = timedelta(task.endedAt - task.createdAt)
        bot.send_message(user_id, f"Анализ завершён за {execution_time.seconds} секунд")
        bot.send_message(user_id, result_stringify(result, " "))


@app.get("/file")
async def get_file(task_id: str):
    task = core.get_task(task_id)
    if task is None:
        return HTTPException(404, "Task not found.")
    filepath = config.MEDIA_DIR / task.filehash
    if not filepath.is_file():
        return HTTPException(410, "File removed.")
    return FileResponse(filepath)
