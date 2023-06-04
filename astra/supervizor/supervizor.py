from dotenv import load_dotenv

load_dotenv("app.env")
from os import environ

environ["SUPERVIZOR"] = "Yes"

import logging

logger = logging.getLogger(__name__)

from astra.core.utils import devport_init, logging_setup

logging_setup(logger)
devport_init()

from astra.core import db

from astra.supervizor import api

app = api.app
