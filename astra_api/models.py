import uuid
from datetime import datetime
import bson

from pydantic import UUID4, BaseModel
from sqlmodel import Field, SQLModel

from .settings import cfg

class BaseBSONModel(BaseModel):
    def bson(self):
        return bson.dumps(self.dict())
    @classmethod
    def parse_raw_bson(cls, data: bytes):
        obj = bson.loads(data)
        return cls.parse_obj(obj)

class SimpleItem(BaseBSONModel): 
    id: UUID4                   = Field()
    hash: int                   = Field()
    model: str                  = Field()
    create_at: datetime         = Field()
    updated_at: datetime        = Field()
    result: bytes|None          = Field(default=None)
    execution_time: int         = Field(default=0)
    
class Item(SimpleItem, SQLModel, table=True):    
    id: UUID4                   = Field(default_factory=uuid.uuid4, primary_key=True)
    file: bytes|None            = Field(default=None, nullable=True)
    hash: int                   = Field(index=True)
    model: str                  = Field(default=cfg.whisper.default_model, index=True)
    create_at: datetime         = Field(default_factory=datetime.now)
    updated_at: datetime        = Field(default_factory=datetime.now)
    result: bytes|None          = Field(default=None, nullable=True)
    execution_time: int         = Field(default=0)

