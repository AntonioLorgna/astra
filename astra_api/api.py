from typing import List
from uuid import uuid4
from fastapi import FastAPI, File, UploadFile, status
from fastapi.responses import RedirectResponse
import astra_api.models as models

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import UUID4
from sqlmodel import Session, select

from astra_api.db import engine, create_db_and_tables
from astra_api.settings import cfg
from astra_api import worker


app = FastAPI()

@app.get("/")
def root_redirect():
    return RedirectResponse("/docs")

@app.post("/items",
    status_code=status.HTTP_202_ACCEPTED,
    
    response_model=models.ItemInput)
def add_item(
    model: str = cfg.whisper.default_model, 
    file: bytes = File(format=[".mp3",".ogg",".flac"], max_length=2<<24)):

    item_input = worker.preprocess_file(file=file, model=model)
    worker.transcribe(item_input.json())
    return item_input

@app.get("/items/{id:uuid}", response_model=models.Item)
def get_document(id: UUID4):
    with Session(engine) as session:
        document = session.get(models.Item, id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return document

@app.delete("/items/{id:uuid}", response_model=models.Item)
def get_document(id: UUID4):
    with Session(engine) as session:
        document = session.get(models.Item, id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        session.delete(document)
        session.commit()
        return document

@app.get("/items/", response_model=List[models.Item])
def get_all_documents(limit: int = 100, offset: int = 0):
    with Session(engine) as session:
        sentence = select(models.Item).limit(limit).offset(offset)
        documents = session.exec(sentence).all()
        if not documents:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return documents


@app.on_event("startup")
def on_startup():
    create_db_and_tables()