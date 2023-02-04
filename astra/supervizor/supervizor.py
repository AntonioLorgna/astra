from dotenv import load_dotenv
load_dotenv('app.env')
from sys import stdout
from pathlib import Path
import os
import logging
from .. import utils


if os.environ.get('DEV', False):
    import debugpy
    debugpy.listen(('0.0.0.0', 7000))
    # debugpy.wait_for_client()

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO) # set logger level
logFormatter = logging.Formatter\
("%(levelname)s: %(message)s")

consoleHandler = logging.StreamHandler(stdout) #set streamhandler to stdout
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

logger.info('Loading...')
MEDIA_DIR = Path(os.environ.get("MEDIA_DIR"))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

from .. import db
db.create_db_and_tables()
from . import api
from .. import celery_worker
from .celery_events import celery_db_syncronization
utils.fire_and_forget(celery_db_syncronization(celery_worker.celery))