from uuid import uuid4
from fastapi import FastAPI, File, UploadFile, status
from fastapi.responses import RedirectResponse
import astra_api.models as models

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import UUID4
from sqlmodel import Session

from astra_api.db import engine
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

@app.get("/documents/{id:uuid}", response_model=models.Item)
def get_document(id: UUID4):
    with Session(engine) as session:
        document = session.get(models.Item, id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return document