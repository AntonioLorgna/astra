from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from astra.api import config


def app_button(text: str):
    web_app = WebAppInfo(url=config.SELF_URL_EXTERNAL)
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text=text, web_app=web_app))
    return kb
