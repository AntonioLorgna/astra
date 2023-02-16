from sys import stdout
from dotenv import load_dotenv
import os

load_dotenv("app.env")
os.environ["FLOWER"] = "Yes"

import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
logFormatter = logging.Formatter("%(levelname)s: %(message)s")

consoleHandler = logging.StreamHandler(stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


from astra import celery

app = celery.app
