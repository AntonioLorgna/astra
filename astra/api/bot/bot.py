import os
from aiogram import types, Dispatcher, Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from logging import getLogger

from astra.api.bot.filters import register_all_filters
from astra.api.bot.handlers import register_all_handlers
from astra.api.bot.utils import get_wh_endpoint

logger = getLogger(__name__)
 
TOKEN = os.environ.get("TG_TOKEN")
if TOKEN is None:
    raise Exception("TG_TOKEN is empty!")
_bot, _dp = None, None
def start_bot():
    global _bot, _dp
    _bot = Bot(token=TOKEN, parse_mode='HTML')
    _dp = Dispatcher(_bot, storage=MemoryStorage())
    register_all_filters(_dp)
    register_all_handlers(_dp)
    Dispatcher.set_current(_dp)
    Bot.set_current(_bot)
    return (_bot, _dp)

async def stop_bot():
    global _bot
    await _bot.session.close()


async def set_bot_webhook():
    global _bot, _dp
    webhook_info = await _bot.get_webhook_info()

    if webhook_info.url == get_wh_endpoint(): return

    await _bot.set_webhook(
        url=get_wh_endpoint()
    )

    logger.info(f"Using webhook url '{get_wh_endpoint()}' for telegram bot.")

async def process_wh_update(update: dict):
    global _bot, _dp
    
    
    telegram_update = types.Update(**update)
    await _dp.process_update(telegram_update)
