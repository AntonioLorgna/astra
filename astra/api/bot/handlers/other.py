from io import BytesIO
from aiogram import Dispatcher
from aiogram.types import Message
from astra import models
from astra.api import core
from astra.api.utils import download_tg_file

from astra.utils import HashIO
from astra.api.utils import build_file_wh, build_status_wh


async def hello(msg: Message):
    await msg.answer('Hello!')

async def process_audio(msg: Message):
    if not any([msg.voice, msg.audio]): return
    downloadable = msg.voice if msg.voice else msg.audio
    
    filepath, hash = await download_tg_file(downloadable, downloadable.file_unique_id)
    filepath.rename(filepath.with_name(hash))
    task_init = models.TaskInit(
        filehash=hash,
        audio_duration=downloadable.duration,
        model='tiny',
        status_webhook=build_status_wh(),
        file_webhook=build_file_wh()
    )
    user = core.get_user_tg(tg_id=str(msg.from_user.id))
    if user is None:
        user = core.add_user_tg(tg_id=str(msg.from_user.id), limit_seconds=1000)
    
    info = core.add_task(user, task_init)
    if info is None:
        msg.answer("К сожалению возникла ошибка при запуске анализа, попробуйте позже.")
        return
    
    msg.answer("Анализ запущен...")
    
    


    
def register_other_handlers(dp: Dispatcher) -> None:
    # todo: register all other handlers
    dp.register_message_handler(hello, commands=['hello'])
    dp.register_message_handler(hello, content_types=['voice', 'audio'])