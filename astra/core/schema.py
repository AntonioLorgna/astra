from datetime import datetime
import celery.states as _states
from typing import List
from pydantic import UUID4, BaseModel, Field, HttpUrl

task_states = _states


class Segment(BaseModel):
    start: float
    end: float
    text: str


class TranscribeResult(BaseModel):

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
    segments: List[Segment]
    datetime_base: datetime

    def to_txt(self, timestamp=False):
        def secs_to_hhmmss(secs: float | int):
            mm, ss = divmod(secs, 60)
            hh, mm = divmod(mm, 60)
            return f"{hh:0>2.0f}:{mm:0>2.0f}:{ss:0>2.0f}"
        
        return "\n".join([
            f"[{secs_to_hhmmss(seg.start)}-{secs_to_hhmmss(seg.end)}] {seg.text.strip()}" 
            if timestamp else seg.text.strip() 
            for seg in self.segments
        ])
    
    def to_srt(self, strip=True):
        def secs_to_hhmmss(secs: float | int):
            mm, ss = divmod(secs, 60)
            hh, mm = divmod(mm, 60)
            return f"{hh:0>2.0f}:{mm:0>2.0f}:{ss:0>6.3f}".replace(".", ",")
        
        srt_str = "\n".join(
            f"{i}\n"
            f'{secs_to_hhmmss(seg.start)} --> {secs_to_hhmmss(seg.end)}\n'
            f'{seg.text.strip() if strip else seg.text}\n'
            for i, seg in enumerate(self.segments, 1)
        )
        return srt_str
        


class TaskInfo(BaseModel):
    id: UUID4
    status: str
    result: str | None = Field(default=None)
    ok: bool = Field(default=True)


class TaskInit(BaseModel):
    audio_duration: float = Field()
    filehash: str = Field()
    model: str = Field()

    status_webhook: HttpUrl = Field()
    file_webhook: HttpUrl = Field()
    user_id: UUID4 = Field()
    account_id: UUID4 = Field()
