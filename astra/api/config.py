from os import environ
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("api.env")
from astra.misc.utils import get_ngrok_hostname


SELF_URL: str = environ.get("SELF_URL")
if SELF_URL is None:
    raise Exception("SELF_URL is empty!")


SUPERVIZOR_URL: str = environ.get("SUPERVIZOR_URL")
if SUPERVIZOR_URL is None:
    raise Exception("SUPERVIZOR_URL is empty!")


SELF_URL_EXTERNAL: str = environ.get("SELF_URL_EXTERNAL")
if SELF_URL_EXTERNAL is None:
    raise Exception("SELF_URL_EXTERNAL is empty!")
if SELF_URL_EXTERNAL == "ngrok":
    SELF_URL_EXTERNAL = get_ngrok_hostname()
    if SELF_URL_EXTERNAL is None:
        raise Exception(
            "SELF_URL_EXTERNAL setted to 'ngrok' but ngrok is not avaliable!"
        )


if environ.get("MEDIA_DIR") is None:
    raise Exception("MEDIA_DIR is empty!")
MEDIA_DIR = Path(environ.get("MEDIA_DIR"))
MEDIA_DIR.mkdir(exist_ok=True, parents=True)


TG_TOKEN: str = environ.get("TG_TOKEN")
if TG_TOKEN is None:
    raise Exception("TG_TOKEN is empty!")


DB_URL = environ.get("DB_URL")
if DB_URL is None:
    raise Exception("DB_URL is empty!")

if environ.get("TG_ADMIN_ID_LIST") is None:
    raise Exception("TG_ADMIN_ID_LIST is empty!")
TG_ADMIN_ID_LIST = environ.get("TG_ADMIN_ID_LIST").split(',')


USE_MODEL = environ.get("USE_MODEL", "tiny")

if environ.get("START_USER_BANK") is None:
    raise Exception("START_USER_BANK is empty!")
START_USER_BANK = int(environ.get("START_USER_BANK"))
