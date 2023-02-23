from os import environ
from dotenv import load_dotenv

load_dotenv("app.env")
environ["SYNC"] = "Yes"

import logging

logger = logging.getLogger(__name__)

from astra.misc.utils import logging_setup, devport_init

logging_setup(logger)
devport_init()


from astra.sync import CeleryTaskSync, app as celery_app

app = CeleryTaskSync(celery_app)
try:
    logger.info("Running celery-db syncronization now")
    app.capture()
except KeyboardInterrupt or SystemExit:
    logger.info("Shutting down celery-db syncronization now")
