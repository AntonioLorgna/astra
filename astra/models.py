from typing import List
from sqlmodel import Field, Relationship, SQLModel
from pydantic import UUID4, HttpUrl
from datetime import datetime
from astra.schema import task_states


class ServiceAccount(SQLModel, table=True):
    __tablename__ = "service_account"
    id: UUID4 = Field(primary_key=True, unique=True)

    service_id: str = Field(primary_key=True, unique=True)
    service_name: str = Field(nullable=False)
    user_id: UUID4 = Field(default=None, foreign_key="user.id")
    user: "User" = Relationship(back_populates="accounts")
    tasks: List["Task"] = Relationship(back_populates="account")
    posts: List["Post"] = Relationship(back_populates="account")


class UserBase(SQLModel):
    id: UUID4 = Field(primary_key=True, unique=True)
    role: int = Field(default=0)
    limit_seconds: int = Field(default=10)


class User(UserBase, table=True):
    accounts: List[ServiceAccount] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="user")
    posts: List["Post"] = Relationship(back_populates="user")


class Result(SQLModel, table=True):
    id: UUID4 = Field(primary_key=True, unique=True)

    filehash: str = Field(index=True)
    model: str = Field(index=True)

    result: str = Field(nullable=False)
    ok: bool = Field()

    posts: List["Post"] = Relationship(back_populates="result")
    tasks: List["Task"] = Relationship(back_populates="result")


class TaskInit(SQLModel):
    filehash: str = Field(index=True)
    audio_duration: float = Field(index=False)
    model: str = Field(index=True)
    status_webhook: HttpUrl | None = Field(default=None)
    file_webhook: HttpUrl = Field()


class Task(TaskInit, table=True):
    id: UUID4 = Field(primary_key=True, unique=True)
    status: str = Field(default=task_states.PENDING)

    reruns: int = Field(default=0)
    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)
    startedAt: datetime | None = Field(default=None, nullable=True)
    endedAt: datetime | None = Field(default=None, nullable=True)

    user_id: UUID4 = Field(foreign_key="user.id")
    account_id: UUID4 = Field(foreign_key="service_account.id")
    result_id: UUID4 | None = Field(default=None, foreign_key="result.id")

    result: Result | None = Relationship(back_populates="tasks")
    user: User = Relationship(back_populates="tasks")
    account: ServiceAccount = Relationship(back_populates="tasks")
    posts: List["Post"] = Relationship(back_populates="task")


class Post(SQLModel, table=True):
    id: UUID4 = Field(primary_key=True, unique=True)

    type: str = Field(default="post")
    status: str = Field(default="visible")
    content: str = Field()

    user_id: UUID4 = Field(foreign_key="user.id")
    account_id: UUID4 = Field(foreign_key="service_account.id")
    task_id: UUID4 = Field(foreign_key="task.id")
    result_id: UUID4 = Field(foreign_key="result.id")

    user: User = Relationship(back_populates="posts")
    account: ServiceAccount = Relationship(back_populates="posts")
    task: Task = Relationship(back_populates="posts")
    result: Result | None = Relationship(back_populates="posts")

    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)
    updatedAt: datetime | None = Field(default=None, nullable=True)
