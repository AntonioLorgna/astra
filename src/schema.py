from pydantic import BaseModel, Field


class TestTaskArgs(BaseModel):
    a: float = Field()
    b: float = Field()
    c: float = Field()

