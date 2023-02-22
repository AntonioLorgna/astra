from dotenv import load_dotenv
load_dotenv('app.env')
from sys import stdout
import os
import logging
from astra.misc.utils import logging_setup, devport_init
logger = logging.getLogger(__name__)
logging_setup(logger)
from astra.sync.celery_events import CeleryTaskSync
from astra.core.celery import app as celery_app

os.environ["SYNC"] = "Yes"
devport_init()
app = CeleryTaskSync(celery_app)
try:
    app.capture()
except KeyboardInterrupt or SystemExit:
    
    logger.info("Shutting down celery-db syncronization now")
