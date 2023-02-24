from aiogram import Dispatcher
from aiogram.types import Message
from sqlmodel import Session
from astra.api import config, core
from astra.api.bot.keyboards.inline import app_button
from astra.core import db, models, schema
from astra.api.utils import download_tg_file, short_uuid
from astra.api.utils import build_file_wh, build_status_wh
from astra.api.bot import templates


async def start(msg: Message):
    # await msg.answer(templates.start_message())
    await msg.answer("test", reply_markup=app_button("app"))


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
            user, account = models.User.create_from_tg(session, tg_id, 0, 1000)
            session.commit()

        task_init = schema.TaskInit(
            status_webhook=build_status_wh(),
            file_webhook=build_file_wh(),
            user_id=user.id,
            account_id=account.id,
            audio_duration=downloadable.duration,
            filehash=hash,
            model=config.USE_MODEL,
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
    dp.register_message_handler(start, commands=["start"])
    dp.register_message_handler(process_audio, content_types=["voice", "audio"])
