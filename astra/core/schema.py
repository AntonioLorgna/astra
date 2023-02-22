from datetime import datetime
import celery.states as _states
from typing import List
from pydantic import UUID4, BaseModel, Field

task_states = _states


class Segment(BaseModel):
    start: float
    end: float
    text: str


class TranscribeResult(BaseModel):
    segments: List[Segment]
    datetime_base: datetime


class TaskInfo(BaseModel):
    id: UUID4
    status: str
    result: str|None = Field(default=None)
    ok: bool = Field(default=True)

