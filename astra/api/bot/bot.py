import os
from pathlib import Path
from aiogram import types, Dispatcher, Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from logging import getLogger

from astra.api.bot.filters import register_all_filters
from astra.api.bot.handlers import register_all_handlers
from astra.api.bot.utils import get_bot_wh_endpoint
from astra.api import config

logger = getLogger(__name__)

def start_bot():
    bot = Bot(token=config.TOKEN, parse_mode='HTML')
    bot.data['MEDIA_DIR'] = Path(os.environ.get('MEDIA_DIR'))
    dp = Dispatcher(bot, storage=MemoryStorage())
    register_all_filters(dp)
    register_all_handlers(dp)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    return (bot, dp)

async def stop_bot():
    s = await Bot.get_current().get_session()
    s.close()


async def set_bot_webhook():
    bot = Bot.get_current()
    webhook_info = await bot.get_webhook_info()

    if webhook_info.url == get_bot_wh_endpoint(): return

    await bot.set_webhook(
        url=get_bot_wh_endpoint()
    )

    logger.info(f"Using webhook url '{get_bot_wh_endpoint()}' for telegram bot.")

async def process_wh_update(update: dict):    
    telegram_update = types.Update(**update)
    await Dispatcher.get_current().process_update(telegram_update)
