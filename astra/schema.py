from datetime import datetime, timedelta
import enum
import celery.states as states
from typing import List
from pydantic import UUID4, BaseModel, Field
from astra import whisper_static
from astra.models import TaskStatus


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

class Segment(BaseModel):
    start: timedelta
    end: timedelta
    text: str

class TranscribeResult(BaseModel):
    segments: List[Segment]
    datetime_base: datetime

class TaskSimpleInfo(BaseModel):
    id: UUID4
    status: TaskStatus

class TaskResult(BaseModel):
    id: UUID4
    model: whisper_static.WhisperModelsNames
    filehash: str
    result: TranscribeResult