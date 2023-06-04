from dotenv import load_dotenv

load_dotenv("app.env")
from astra.core.utils import logging_setup
import os

os.environ["FLOWER"] = "Yes"

import logging

logger = logging.getLogger(__name__)
logging_setup(logger)


from astra.core import celery

app = celery.app
