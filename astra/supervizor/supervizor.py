from dotenv import load_dotenv

load_dotenv("app.env")
from os import environ

environ["SUPERVIZOR"] = "Yes"

import logging

logger = logging.getLogger(__name__)

from astra.misc.utils import devport_init, logging_setup

logging_setup(logger)
devport_init()

from astra.core import db

db.create_db_and_tables()
from astra.supervizor import api

app = api.app
