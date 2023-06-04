from os import environ
from dotenv import load_dotenv
load_dotenv('worker.env')
from pathlib import Path
from astra.core.utils import get_envvar



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



MEDIA_DIR = Path(get_envvar(environ, "MEDIA_DIR"))
MEDIA_DIR.mkdir(exist_ok=True)

DTLN_ONNX_MODEL_1_PATH = Path(get_envvar(environ, "DTLN_ONNX_MODEL_1_PATH"))
if not DTLN_ONNX_MODEL_1_PATH.is_file():
    raise FileNotFoundError(f"Cannot find 'DTLN_ONNX_MODEL_1_PATH' by path '{DTLN_ONNX_MODEL_1_PATH}'")

DTLN_ONNX_MODEL_2_PATH = Path(get_envvar(environ, "DTLN_ONNX_MODEL_2_PATH"))
if not DTLN_ONNX_MODEL_2_PATH.is_file():
    raise FileNotFoundError(f"Cannot find 'DTLN_ONNX_MODEL_2_PATH' by path '{DTLN_ONNX_MODEL_2_PATH}'")

WHISPER_CT2_MODEL_DIR = Path(get_envvar(environ, "WHISPER_CT2_MODEL_DIR"))
if not WHISPER_CT2_MODEL_DIR.is_dir():
    raise FileNotFoundError(f"Cannot find 'WHISPER_CT2_MODEL_DIR' by path '{WHISPER_CT2_MODEL_DIR}'")

WHISPER_DEVICE = get_envvar(environ, "WHISPER_DEVICE")
WHISPER_COMPUTE_TYPE = get_envvar(environ, "WHISPER_COMPUTE_TYPE", empty_ok=True)
