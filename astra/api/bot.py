import hashlib
import os, base64
from aiogram import Dispatcher, Bot, types
from logging import getLogger
from astra.utils import get_ngrok_hostname

from urllib.parse import quote
logger = getLogger(__name__)

TOKEN = os.environ.get("TG_TOKEN")
if TOKEN is None:
    raise Exception("TG_TOKEN is empty!")

HOSTNAME = os.environ.get("HOSTNAME")
if HOSTNAME is None:
    HOSTNAME = get_ngrok_hostname()
    
if HOSTNAME is None:
    raise Exception("HOSTNAME is empty!")
    
_wh_path = None
def get_wh_path():
    global _wh_path
    if _wh_path is not None: return _wh_path

    token_hash = base64.urlsafe_b64encode(hashlib.sha256(TOKEN.encode('utf-8')).digest()).replace(b'=', b'').decode('utf-8')
    _wh_path = f"/bot/{quote(token_hash)}"
    return _wh_path


def get_wh_endpoint():
    return HOSTNAME + get_wh_path()



bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands="start")
async def start(message: types.Message):
    await message.answer(f"Hello, {message.from_user.full_name}")