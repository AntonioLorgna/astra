from dotenv import load_dotenv
load_dotenv('app.env')
from sys import stdout
import os
import logging
from astra.utils import logging_setup
logger = logging.getLogger(__name__)
logging_setup(logger)
from astra.sync.celery_events import CeleryTaskSync
from astra.core.celery import app as celery_app

os.environ["SYNC"] = "Yes"


if os.environ.get("DEV_PORT") is not None:
    port = int(os.environ.get("DEV_PORT"))
    import debugpy
    debugpy.listen(('0.0.0.0', port))
    # debugpy.wait_for_client()

app = CeleryTaskSync(celery_app)
try:
    app.capture()
except KeyboardInterrupt or SystemExit:
    
    logger.info("Shutting down celery-db syncronization now")
