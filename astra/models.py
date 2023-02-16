from typing import List
from sqlmodel import Field, Relationship, SQLModel
from pydantic import UUID4, HttpUrl
from datetime import datetime
from astra.schema import task_states

class UserTaskLink(SQLModel, table=True):
    user_id: UUID4 = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    task_id: UUID4 = Field(
        default=None, foreign_key="task.id", primary_key=True
    )

class UserServiceAccount(SQLModel, table=True):
    __tablename__ = "user_service_account"
    id: UUID4 = Field(primary_key=True, unique=True)

    service_id: str = Field(primary_key=True, unique=True)
    service_name: str = Field(nullable=False)
    user_id: UUID4 = Field(default=None, foreign_key="user.id")
    user: "User" = Relationship(back_populates="user")


class UserBase(SQLModel):
    id: UUID4 = Field(primary_key=True, unique=True)
    role: int = Field(default=0)
    limit_seconds: int = Field(default=-1)


class User(UserBase, table=True):
    service_accounts: List["UserServiceAccount"] = Relationship(
        back_populates="user_service_account"
    )

    tasks: List["Task"] = Relationship(back_populates="users", link_model=UserTaskLink)
    posts: List["Post"] = Relationship(back_populates="post")



class Result(SQLModel, table=True):
    id: UUID4 = Field(primary_key=True, unique=True)

    task_id: UUID4 = Field(foreign_key="task.id")
    task: "Task" = Relationship(back_populates="task")

    result: str = Field(nullable=False)
    ok: bool = Field()

class TaskBase(SQLModel):
    id: UUID4 = Field(primary_key=True, unique=True)
    status: str = Field(default=task_states.PENDING)

    filehash: str = Field(index=True)
    audio_duration: float = Field(index=False)
    model: str = Field(index=True)
    status_webhook: HttpUrl | None = Field(default=None)
    file_webhook: HttpUrl = Field()

    reruns: int = Field(default=0)
    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)
    startedAt: datetime | None = Field(default=None, nullable=True)
    endedAt: datetime | None = Field(default=None, nullable=True)

    result_id: UUID4 | None = Field(default=None, foreign_key="result.id")


class Task(TaskBase, table=True):
    users: List["User"] = Relationship(back_populates="tasks", link_model=UserTaskLink)
    result: Result | None = Relationship(back_populates="result")

    # result: Dict = Field(default={}, sa_column=Column(JSON))
    # class Config:
    #     arbitrary_types_allowed = True



class PostBase(SQLModel):
    id: UUID4 = Field(primary_key=True, unique=True)

    type: str = Field(default="post")
    status: str = Field(default="visible")
    content: str = Field()

    user_id: UUID4 = Field(foreign_key="user.id")
    task_id: UUID4 = Field(foreign_key="task.id")

    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)
    updatedAt: datetime | None = Field(default=None, nullable=True)


class Post(PostBase, table=True):
    user: "User" = Relationship(back_populates="user")
    task: "Task" = Relationship(back_populates="task")
