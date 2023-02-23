from os import environ
from dotenv import load_dotenv
load_dotenv('worker.env')
from pathlib import Path


CELERY_BROKER_URL = environ.get('CELERY_BROKER_URL')
if CELERY_BROKER_URL is None:
    raise ValueError("CELERY_BROKER_URL is empty!")

CELERY_RESULT_BACKEND = environ.get('CELERY_RESULT_BACKEND')
if CELERY_RESULT_BACKEND is None:
    raise ValueError("CELERY_RESULT_BACKEND is empty!")

SUPERVIZOR_FILES_URL = environ.get('SUPERVIZOR_FILES_URL')
if SUPERVIZOR_FILES_URL is None:
    raise ValueError("SUPERVIZOR_FILES_URL is empty!")

WHISPER_AVALIABLE_MODELS = environ.get('WHISPER_AVALIABLE_MODELS')
if WHISPER_AVALIABLE_MODELS is None:
    raise ValueError("WHISPER_AVALIABLE_MODELS is empty!")

if environ.get('WHISPER_MODELS_DIR') is None:
    raise ValueError("WHISPER_MODELS_DIR is empty!")
WHISPER_MODELS_DIR = Path(environ.get('WHISPER_MODELS_DIR'))
WHISPER_MODELS_DIR.mkdir(exist_ok=True)
