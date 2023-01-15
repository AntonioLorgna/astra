from urllib.parse import urlparse
from datetime import datetime

import dramatiq, bson
from dramatiq.brokers.redis import RedisBroker
from sqlmodel import Session, select, or_, and_

from _astra_api.db import engine
from _astra_api.models import Item
from _astra_api.whisper import Whisper
from _astra_api.settings import cfg


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

class BSONEncoder(dramatiq.encoder.Encoder):
    encode = bson.dumps
    decode = bson.loads

dramatiq.set_encoder(BSONEncoder)


@dramatiq.actor
def transcribe(item_bson: bytes):
    item = Item(**bson.loads(item_bson))
    item_bson = None
    with Session(engine) as session:
        sentence = select(Item).where(or_(Item.id == item.id, and_(Item.hash == item.hash, Item.model == item.model))).limit(1)
        item_db = session.exec(sentence).one_or_none()

        if item_db is None:
            item_db = Item(**item.dict())
        else:
            item_dict = item.dict(exclude_unset=True)
            for key, value in item_dict.items():
                setattr(item_db, key, value)
        item_db.result = Whisper.transcribe(item_db.file, item_db.model)
        item_db.updated_at = datetime.utcnow()

        session.add(item_db)
        session.commit()
