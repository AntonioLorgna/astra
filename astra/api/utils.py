from pathlib import Path
from aiogram.types.mixins import Downloadable
from pydantic import UUID4
from urllib.parse import quote
from functools import lru_cache

from astra.api import config
from astra.misc.utils import HashIO
from astra.api import config


async def download_tg_file(
    downloadable: Downloadable, temp_filename: str, timeout=35, chunk_size=65536
):
    bot = downloadable.bot

    temp_filepath: Path = bot.data.get("MEDIA_DIR") / temp_filename

    file = await downloadable.get_file()
    url = bot.get_file_url(file.file_path)
    session = await bot.get_session()
    async with session.get(
        url,
        timeout=timeout,
        proxy=bot.proxy,
        proxy_auth=bot.proxy_auth,
        raise_for_status=True,
    ) as response:
        hash = HashIO()
        with open(temp_filepath, "wb") as f:
            while True:
                chunk = await response.content.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                hash.update(chunk)

    return (temp_filepath, str(hash))


def build_status_wh():
    return f"{config.SELF_URL}/status"


def build_file_wh():
    return f"{config.SELF_URL}/file"


def short_uuid(id: str | UUID4, lenght: int = 8):
    return str(id).split("-")[0][:lenght]


@lru_cache(maxsize=None)
def get_bot_wh_path():
    hash = HashIO().update(config.TG_TOKEN.encode("utf-8"))
    token_hash = str(hash)
    return f"/bot/{quote(token_hash)}"


@lru_cache(maxsize=None)
def get_bot_wh_url():
    return config.SELF_URL_EXTERNAL + get_bot_wh_path()
