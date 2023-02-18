from os import environ
from pathlib import Path


SELF_ADDRESS: str = environ.get('SELF_ADDRESS')
if SELF_ADDRESS is None:
    raise Exception("SELF_ADDRESS is empty!")
SUPERVIZOR_ADDRESS: str = environ.get('SUPERVIZOR_ADDRESS')
if SUPERVIZOR_ADDRESS is None:
    raise Exception("SUPERVIZOR_ADDRESS is empty!")

TG_WH_HOSTNAME: str = environ.get("TG_WH_HOSTNAME")
if TG_WH_HOSTNAME is None:
    raise Exception("TG_WH_HOSTNAME is empty!")
    
if environ.get("MEDIA_DIR") is None:
    raise Exception("MEDIA_DIR is empty!")
MEDIA_DIR = Path(environ.get("MEDIA_DIR"))
MEDIA_DIR.mkdir(exist_ok=True)

TOKEN: str = environ.get("TG_TOKEN")
if TOKEN is None:
    raise Exception("TG_TOKEN is empty!")
