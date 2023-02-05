from typing import Dict
from sqlmodel import JSON, Column, Field, SQLModel, Enum
from pydantic import UUID4
from datetime import datetime
from astra import whisper_static
from astra.schema import TaskStatus

class Task(SQLModel, table=True):
    id: UUID4 = Field(primary_key=True, unique=True)

    filehash: str = Field(index=True, max_length=40)
    model: whisper_static.WhisperModelsNames = Field(index=True, sa_column=Enum(whisper_static.WhisperModelsNames))
    args: Dict = Field(default={}, sa_column=Column(JSON))

    status: TaskStatus = Field(default=TaskStatus.PENDING, sa_column=Enum(TaskStatus))
    result: Dict = Field(default={}, sa_column=Column(JSON))
    reruns: int = Field(default=0)

    webhook: str|None = Field(default=None, max_length=2048)
    user: int = Field(index=True, default=0)
    category: int = Field(index=True, default=0)

    createdAt: datetime = Field(default_factory=datetime.now)
    startedAt: datetime = Field(default=None, nullable=True)
    endedAt: datetime = Field(default=None, nullable=True)

    class Config:
        arbitrary_types_allowed = True



