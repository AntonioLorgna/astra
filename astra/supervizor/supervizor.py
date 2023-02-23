from dotenv import load_dotenv
load_dotenv('app.env')
from sys import stdout
from pathlib import Path
import os
import logging

os.environ["SUPERVIZOR"] = "Yes"


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
    # logger.warn("deb")
    debugpy.listen(('0.0.0.0', port))
    # debugpy.wait_for_client()


from astra.core import db, models
db.create_db_and_tables()
from astra.supervizor import api
app = api.app
from astra.core import celery