from datetime import datetime, timedelta
from typing import List
from pydantic import UUID4, BaseModel, Field
from astra import whisper_static
from astra.models import TaskStatus

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