from typing import List
from uuid import uuid4
from sqlmodel import Field, Relationship, SQLModel, Session, select
from pydantic import UUID4, HttpUrl
from datetime import datetime
from astra.schema import task_states
from sqlalchemy import func



class ServiceAccount(SQLModel, table=True):
    __tablename__ = "service_account"
    id: UUID4 = Field(default_factory=uuid4, primary_key=True, unique=True)

    service_id: str = Field(index=True)
    service_name: str = Field(nullable=False)
    user_id: UUID4 = Field(default=None, foreign_key="user.id")
    user: "User" = Relationship(back_populates="accounts")
    tasks: List["Task"] = Relationship(back_populates="account")
    posts: List["Post"] = Relationship(back_populates="account")


class UserBase(SQLModel):
    id: UUID4 = Field(default_factory=uuid4, primary_key=True, unique=True)
    role: int = Field(default=0)
    limit_seconds: int = Field(default=10)


class User(UserBase, table=True):
    accounts: List[ServiceAccount] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="user")
    posts: List["Post"] = Relationship(back_populates="user")


class Job(SQLModel, table=True):
    id: UUID4 = Field(default_factory=uuid4, primary_key=True, unique=True)

    filehash: str = Field(index=True)
    model: str = Field(index=True)
    model_quality: int = Field()

    status: str = Field(default=task_states.PENDING)
    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)
    startedAt: datetime | None = Field(default=None)
    endedAt: datetime | None = Field(default=None)

    result: str | None = Field(default=None)

    tasks: List["Task"] = Relationship(back_populates="job")

    def get_queue_position(self, session: Session):
        statement = select([func.count(Job.id)]).where(
            Job.createdAt < self.createdAt,
            Job.endedAt == None,
            Job.startedAt != None
        )
        return session.exec(statement).one()


class TaskInit(SQLModel):
    filehash: str = Field(index=True)
    audio_duration: float = Field(index=False)
    model: str = Field(index=True)
    status_webhook: HttpUrl | None = Field(default=None)
    file_webhook: HttpUrl = Field()
    user_id: UUID4 = Field(foreign_key="user.id")
    account_id: UUID4 = Field(foreign_key="service_account.id")


class Task(TaskInit, table=True):
    id: UUID4 = Field(default_factory=uuid4, primary_key=True, unique=True)

    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)

    job_id: UUID4 = Field(foreign_key="job.id")
    job: Job = Relationship(back_populates="tasks")
    user: User = Relationship(back_populates="tasks")
    account: ServiceAccount = Relationship(back_populates="tasks")
    posts: List["Post"] = Relationship(back_populates="task")


class Post(SQLModel, table=True):
    id: UUID4 = Field(default_factory=uuid4, primary_key=True, unique=True)

    type: str = Field(default="post")
    status: str = Field(default="visible")
    title: str = Field(default="")
    content: str = Field()

    user_id: UUID4 = Field(foreign_key="user.id")
    account_id: UUID4 = Field(foreign_key="service_account.id")
    task_id: UUID4 = Field(foreign_key="task.id")

    user: User = Relationship(back_populates="posts")
    account: ServiceAccount = Relationship(back_populates="posts")
    task: Task = Relationship(back_populates="posts")

    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)
    updatedAt: datetime | None = Field(default=None, nullable=True)
