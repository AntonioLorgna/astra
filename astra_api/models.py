import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Optional
from fastapi import File, UploadFile

from pydantic import UUID4, BaseModel
from sqlmodel import Field, SQLModel

from .settings import cfg

_models_literal = Literal[tuple(cfg.whisper.models)] # type: ignore

class ItemInputForm(BaseModel):
    file: bytes = File(format=[".mp3",".ogg",".flac"], max_length=2<<24)
    model: _models_literal


class ItemInput(SQLModel):    
    id: UUID4  = Field(primary_key=True)
    filepath: Path | None
    hash: int = Field(index=True)
    model: _models_literal
    create_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Item(ItemInput):    
    result: dict
    execution_time: timedelta