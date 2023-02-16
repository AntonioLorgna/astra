from dotenv import load_dotenv
load_dotenv('app.env')
from sys import stdout
import os
import logging
from astra.sync.celery_events import CeleryTaskSync
from astra.celery import app as celery_app

os.environ["SYNC"] = "Yes"


logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO) # set logger level
logFormatter = logging.Formatter\
("%(levelname)s: %(message)s")

consoleHandler = logging.StreamHandler(stdout) #set streamhandler to stdout
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


if os.environ.get("DEV_PORT") is not None:
    port = int(os.environ.get("DEV_PORT"))
    import debugpy
    debugpy.listen(('0.0.0.0', port))
    # debugpy.wait_for_client()

app = CeleryTaskSync(celery_app)
app.capture()