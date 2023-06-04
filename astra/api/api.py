from datetime import timedelta
from pathlib import Path
from uuid import UUID
from aiogram import Bot, Dispatcher
from fastapi import Body, FastAPI, HTTPException, Header, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from sqlmodel import Session
from astra.api import config
from astra.api.bot.keyboards.inline import edit_post
from astra.api.bot.states import CREATE_POST
from astra.core import db, models, schema
from astra.api.bot import (
    start_bot,
    stop_bot,
    set_bot_webhook,
    process_wh_update,
)
from astra.api.utils import short_uuid, get_bot_wh_path
from astra.core.utils import result_stringify, logging_setup, devport_init
import logging
import orjson
from aiogram.dispatcher import FSMContext
from aiogram.utils import web_app

logger = logging.getLogger(__name__)
logging_setup(logger)

devport_init()

app = FastAPI()
start_bot()


@app.get("/api/test")
def test_helloworld():
    return "Hello World!"


@app.on_event("startup")
async def on_startup():
    # TG
    await set_bot_webhook()


@app.on_event("shutdown")
async def on_shutdown():
    # TG
    await stop_bot()


app.post(get_bot_wh_path())(process_wh_update)
logger.info(get_bot_wh_path())


@app.post("/api/status")
async def process_task_status(task_info: schema.TaskInfo, already_done=False):
    bot = Bot.get_current()

    with Session(db.engine) as session:
        task = session.get(models.Task, task_info.id)
        if task is None:
            raise HTTPException(
                404,
                f"Task with id '{task_info.id}' does not exist, but task_info contains it",
            )
        user_id = task.account.service_id
        job = task.job
        if job is None:
            raise HTTPException(404, f"Task with id '{task_info.id}' does not have Job")

        if task_info.status != schema.task_states.SUCCESS:
            position = job.get_queue_position(session)
            if position == 0:
                await bot.send_message(
                    user_id,
                    f"#T{short_uuid(task_info.id)} Статус: {task_info.status}, в обработке",
                )
            else:
                await bot.send_message(
                    user_id,
                    f"#T{short_uuid(task_info.id)} Статус: {task_info.status}, позиция в очереди: {position}",
                )
            return
        result = schema.TranscribeResult(**orjson.loads(task_info.result))
        execution_time: timedelta = job.endedAt - job.startedAt
        waiting_time: timedelta = job.startedAt - job.createdAt

        dp = Dispatcher.get_current()
        # state: FSMContext = await dp.storage.get_state(user=user_id)
        state = FSMContext(dp.storage, chat=user_id, user=user_id)
        await state.set_state(CREATE_POST)
        await state.set_data({"task_id": task.id})

        if already_done:
            post_exist = len(task.posts) > 0

            if not post_exist:
                post = models.Post.create_from(session, task)
                session.commit()

            post = task.posts[-1]
            reply_markup = edit_post(post_id=post.id)

            await bot.send_message(
                user_id,
                f"#T{short_uuid(task_info.id)} Анализ данной записи уже был произведён.",
                reply_markup=reply_markup,
            )
            return
        

        post = models.Post.create_from(session, task)
        session.commit()

        await bot.send_message(
            user_id,
            f"#T{short_uuid(task_info.id)} Анализ завершён за {execution_time.seconds} сек."
            f" Ожидание в очереди составило {waiting_time.seconds} сек.",
            reply_markup=edit_post(post_id=post.id),
        )


@app.get("/api/file")
async def get_file(job_id: str = Body(embed=True)):
    with Session(db.engine) as session:
        job = session.get(models.Job, job_id)
        if job is None:
            raise HTTPException(404, f"job not found ({job_id})")
        filepath = config.MEDIA_DIR / job.filehash
        if not filepath.is_file():
            raise HTTPException(410, "File removed.")
        return FileResponse(filepath)


@app.get("/api/post/{post_id}")
async def get_post(post_id: str, initData: str = Header(default=None)):
    is_web_app = web_app.check_webapp_signature(config.TG_TOKEN, initData)
    if not is_web_app and config.DISABLE_WEBAPP_ONLY_FROM_TG:
        raise HTTPException(401, f"Use Telegram web app to open this page!")
    try:
        UUID(post_id)
    except ValueError as e:
        raise HTTPException(422, f"Badly formed UUID ({post_id})")
    logger.warn(initData)
    with Session(db.engine) as session:
        post = session.get(models.Post, post_id)
        if post is None:
            raise HTTPException(404, f"Post not found ({post_id})")
        return post


@app.post("/api/post/{post_id}")
async def set_post_content(post_id: str, content: schema.TranscribeResult, initData: str = Header(default=None)):
    is_web_app = web_app.check_webapp_signature(config.TG_TOKEN, initData)
    if not is_web_app and config.DISABLE_WEBAPP_ONLY_FROM_TG:
        raise HTTPException(401, f"Use Telegram web app to open this page!")
    try:
        UUID(post_id)
    except ValueError as e:
        raise HTTPException(422, f"Badly formed UUID ({post_id})")
    logger.warn(initData)
    with Session(db.engine) as session:
        post = session.get(models.Post, post_id)
        if post is None:
            raise HTTPException(404, f"Post not found ({post_id})")
        post.set_content(content)
        session.commit()
        return post


app.mount("/", StaticFiles(directory="./frontend/dist", html=True), name="static")
