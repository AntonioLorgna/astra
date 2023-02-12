from typing import Dict, List
from sqlmodel import JSON, Column, Field, Relationship, SQLModel, Enum
from pydantic import UUID4
from datetime import datetime
from astra import whisper_static
from astra.schema import TaskStatus

class UserServiceAccount(SQLModel, table=True):
    __tablename__ = "user_service_account"
    id: UUID4 = Field(primary_key=True, unique=True)

    service_id: str = Field(primary_key=True, unique=True)
    service_name: str = Field(nullable=False)
    user_id: UUID4 = Field(default=None, foreign_key="user.id")
    user: 'User' = Relationship(back_populates="user")

class UserBase(SQLModel):
    id: UUID4 = Field(primary_key=True, unique=True)
    role: int = Field(default=0)
    limit_seconds: int = Field(default=-1)

class User(UserBase, table=True):
    service_accounts: List['UserServiceAccount'] = Relationship(back_populates="user_service_account")
    tasks: List['Task'] = Relationship(back_populates="task")
    posts: List['Post'] = Relationship(back_populates="post")


class TaskBase(SQLModel):
    id: UUID4 = Field(primary_key=True, unique=True)
    status: TaskStatus = Field(default=TaskStatus.PENDING, sa_column=Enum(TaskStatus))

    filehash: str = Field(index=True)
    audio_duration: float = Field(index=False)
    model: whisper_static.WhisperModelsNames = Field(index=True, sa_column=Enum(whisper_static.WhisperModelsNames))
    result_webhook: str|None = Field(default=None, max_length=2048)
    file_webhook: str = Field(max_length=2048)

    reruns: int = Field(default=0)
    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)
    startedAt: datetime|None = Field(default=None, nullable=True)
    endedAt: datetime|None = Field(default=None, nullable=True)

    user_id: UUID4 = Field(foreign_key="user.id")
    result_id: UUID4|None = Field(default=None, foreign_key="result.id")


class Task(TaskBase, table=True):
    user: 'User' = Relationship(back_populates="user")
    result: 'Result'|None = Relationship(back_populates="result")

    # result: Dict = Field(default={}, sa_column=Column(JSON))
    # class Config:
    #     arbitrary_types_allowed = True

class Result(SQLModel, table=True):
    id: UUID4 = Field(primary_key=True, unique=True)

    task_id: UUID4 = Field(foreign_key="task.id")
    task: 'Task' = Relationship(back_populates="task")

    result: str = Field(nullable=False)
    ok: bool = Field()

class PostBase(SQLModel):
    id: UUID4 = Field(primary_key=True, unique=True)

    type: str = Field(default='post')
    status: str = Field(default='visible')
    content: str = Field()

    user_id: UUID4 = Field(foreign_key="user.id")
    task_id: UUID4 = Field(foreign_key="task.id")

    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)
    updatedAt: datetime|None = Field(default=None, nullable=True)
    

class Post(PostBase, table=True):
    user: 'User' = Relationship(back_populates="user")
    task: 'Task' = Relationship(back_populates="task")
