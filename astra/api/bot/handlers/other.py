from io import BytesIO
import uuid
from aiogram import Dispatcher
from aiogram.types import Message
from sqlmodel import Session
from astra.core import models
from astra.api import config, core
from astra.core import db
from astra.api.utils import download_tg_file, short_uuid

from astra.misc.utils import HashIO
from astra.api.utils import build_file_wh, build_status_wh


async def hello(msg: Message):
    await msg.answer("Hello!")


async def process_audio(msg: Message):
    if not any([msg.voice, msg.audio]):
        return
    downloadable = msg.voice if msg.voice else msg.audio

    filepath, hash = await download_tg_file(downloadable, downloadable.file_unique_id)
    filepath.rename(filepath.with_name(hash))

    tg_id = str(msg.from_user.id)

    with Session(db.engine) as session:
        user, account = models.User.get_from_account_tg(session, tg_id)
        if not (account or user):
            user, account = models.User.create_from_tg(
                session, tg_id, session, 1000
            )

        task_init = models.TaskBase(
            filehash=hash,
            audio_duration=downloadable.duration,
            model=config.USE_MODEL,
            status_webhook=build_status_wh(),
            file_webhook=build_file_wh(),
            user_id=user.id,
            account_id=account.id,
        )
    info = await core.add_task(task_init)
    if info is None:
        await msg.answer(
            "К сожалению возникла ошибка при запуске анализа, попробуйте позже."
        )
        return
    if info.result is not None:
        await core.result_exist(info, msg.bot, tg_id)
        return
    await msg.answer(f"#T{short_uuid(info.id)} Анализ запущен...")


def register_other_handlers(dp: Dispatcher) -> None:
    # todo: register all other handlers
    dp.register_message_handler(hello, commands=["hello"])
    dp.register_message_handler(process_audio, content_types=["voice", "audio"])
