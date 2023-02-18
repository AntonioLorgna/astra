from io import BytesIO
from aiogram import Dispatcher
from aiogram.types import Message
from astra.api.utils import download_tg_file

from astra.utils import HashIO


async def echo(msg: Message):
    # todo: remove echo example:3
    await msg.answer(msg.text)

async def process_audio(msg: Message):
    if not any([msg.voice, msg.audio]): return
    downloadable = msg.voice if msg.voice else msg.audio
    
    filepath, hash = await download_tg_file(downloadable, downloadable.file_unique_id)
    filepath.rename(filepath.with_name(hash))
    


    
def register_other_handlers(dp: Dispatcher) -> None:
    # todo: register all other handlers
    dp.register_message_handler(echo, content_types=['text'])