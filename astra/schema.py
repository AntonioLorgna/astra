from datetime import datetime
import celery.states as _states
from typing import List
from pydantic import UUID4, BaseModel

task_states = _states


class Segment(BaseModel):
    start: float
    end: float
    text: str


class TranscribeResult(BaseModel):
    segments: List[Segment]
    datetime_base: datetime


class TaskSimpleInfo(BaseModel):
    id: UUID4
    status: str


class TaskResult(BaseModel):
    id: UUID4
    model: str
    filehash: str
    result: TranscribeResult
