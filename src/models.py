from typing import Dict
from sqlmodel import JSON, Column, Field, SQLModel, Enum, DateTime
from pydantic import UUID4, BaseModel
import celery.states as states
from celery.result import AsyncResult
import enum
from datetime import datetime
from . import whisper_static

class TaskStatus(str, enum.Enum):
    FAILURE = states.FAILURE
    PENDING = states.PENDING
    RETRY = states.RETRY
    REVOKED = states.REVOKED
    STARTED = states.STARTED
    SUCCESS = states.SUCCESS
    SENT = 'SENT'
    REJECTED = states.REJECTED
    RECEIVED = states.RECEIVED

class TaskSimpleInfo(BaseModel):
    id: UUID4
    status: TaskStatus

class Task(SQLModel, table=True):
    id: UUID4 = Field(primary_key=True, unique=True)

    filehash: int = Field(index=True)
    model: whisper_static.WhisperModelsNames = Field(index=True, sa_column=Enum(whisper_static.WhisperModelsNames))
    args: Dict = Field(default={}, sa_column=Column(JSON))

    status: TaskStatus = Field(default=TaskStatus.PENDING, sa_column=Enum(TaskStatus))
    result: Dict = Field(default={}, sa_column=Column(JSON))
    reruns: int = Field(default=0)

    user: int = Field(index=True, default=0)
    category: int = Field(index=True, default=0)

    createdAt: datetime = Field(default_factory=datetime.now)
    startedAt: datetime = Field(default=None, nullable=True)
    endedAt: datetime = Field(default=None, nullable=True)

    class Config:
        arbitrary_types_allowed = True

    