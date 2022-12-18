import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import UUID4
from sqlmodel import Field, SQLModel

from .settings import cfg

class ItemInput(SQLModel):    
    id: UUID4                   = Field(default_factory=uuid.uuid4, primary_key=True)
    filepath: str | None       = Field(default=None, nullable=True)
    hash: int                   = Field(index=True)
    model: str                  = Field(default=cfg.whisper.default_model, index=True)
    create_at: datetime         = Field(default_factory=datetime.now)
    updated_at: datetime        = Field(default_factory=datetime.now)

class Item(ItemInput, table=True): 
    result: str                 = Field()
    execution_time: timedelta   = Field(default=timedelta(0))