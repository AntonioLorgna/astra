from dotenv import load_dotenv
load_dotenv('app.env')
from astra.core.celery import app
from astra.sync.celery_events import CeleryTaskSync