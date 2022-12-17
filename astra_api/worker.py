from urllib.parse import urlparse
from datetime import datetime
from zlib import crc32

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from sqlmodel import Session, select, or_

from astra_api.db import engine
from astra_api.models import Item, ItemInput
from astra_api.whisper import Whisper
from astra_api.settings import cfg


redis_parameters = urlparse(cfg.taskqueue.broker_uri)
redis_broker = RedisBroker(
    host=redis_parameters.hostname,
    port=redis_parameters.port,
    username=redis_parameters.username,
    password=redis_parameters.password,
    # Heroku Redis with TLS use self-signed certs, so we need to tinker a bit
    ssl=redis_parameters.scheme == "rediss",
    ssl_cert_reqs=None,
)
dramatiq.set_broker(redis_broker)


def preprocess_file(file: bytes, model: str):
    item = ItemInput(
        hash=crc32(file) + len(file),
        model=model)

    item.filepath = cfg.temp_directory / str(item.id)
    with open(item.filepath, 'wb') as f:
        f.write(file)
    
    return item

@dramatiq.actor
def transcribe(item_json: str):
    item = ItemInput.parse_raw(item_json)
    with Session(engine) as session:
        item_db = session.get(Item, item.id)

        if item_db is None:
            item_db = Item(**item.dict())
        else:
            item_dict = item.dict(exclude_unset=True)
            for key, value in item_dict.items():
                setattr(item_db, key, value)

        item_db.result = Whisper.transcribe(item_db.filepath, item_db.model)
        item_db.updated_at = datetime.utcnow()

        if cfg.taskqueue.remove_source_files:
            item_db.filepath.unlink(missing_ok=True)
            item_db.filepath = None

        session.add(item_db)
        session.commit()
