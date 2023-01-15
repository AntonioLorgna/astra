from typing import List
from zlib import crc32
from fastapi import FastAPI, File, status
from fastapi.responses import RedirectResponse
import astra_api.models as models

from fastapi import FastAPI, HTTPException, status
from pydantic import UUID4
from sqlmodel import Session, select

from astra_api.db import engine, create_db_and_tables
from astra_api.settings import cfg
from astra_api import worker

if cfg.dev:
    import debugpy
    debugpy.listen(('0.0.0.0', 5678))


app = FastAPI()

@app.get("/")
def root_redirect():
    return RedirectResponse("/docs")

@app.post("/items",
    status_code=status.HTTP_202_ACCEPTED)
def add_item(
    model: str = cfg.whisper.default_model, 
    file: bytes = File(format=[".mp3",".ogg",".flac"], max_length=2<<24)):
    
    hash = crc32(file)^len(file)

    item = models.Item(
        file=file,
        model=model,
        hash=hash
    )
    worker.transcribe(item.bson())
    return models.SimpleItem.parse_obj(item)

@app.get("/items/{id:uuid}")
def get_item(id: UUID4):
    with Session(engine) as session:
        item = session.get(models.Item, id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return models.SimpleItem.parse_obj(item)


@app.delete("/items/{id:uuid}")
def get_item(id: UUID4):
    with Session(engine) as session:
        item = session.get(models.Item, id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        session.delete(item)
        session.commit()
        return models.SimpleItem.parse_obj(item)

@app.get("/items/", response_model=List[models.Item])
def get_all_items(limit: int = 100, offset: int = 0):
    with Session(engine) as session:
        sentence = select(models.Item).limit(limit).offset(offset)
        items = session.exec(sentence).all()
        if not items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return [models.SimpleItem.parse_obj(item) for item in items]


@app.on_event("startup")
def on_startup():
    create_db_and_tables()