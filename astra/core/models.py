from typing import List
from uuid import uuid4
import orjson
from sqlmodel import Field, Relationship, SQLModel, Session, select
from pydantic import UUID4, HttpUrl
from datetime import datetime
from astra.core.schema import TranscribeResult, task_states
from sqlalchemy import func
from astra.misc.utils import result_stringify, short_uuid

from astra.static.whisper_models import WhisperModels


class ServiceAccountBase(SQLModel):
    service_id: str = Field(index=True)
    service_name: str = Field(nullable=False)
    user_id: UUID4|None = Field()


class ServiceAccount(ServiceAccountBase, table=True):
    __tablename__ = "service_account"
    id: UUID4 = Field(default_factory=uuid4, primary_key=True, unique=True)

    user_id: UUID4 = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="accounts")
    tasks: List["Task"] = Relationship(back_populates="account")


class UserBase(SQLModel):
    id: UUID4 = Field(default_factory=uuid4, primary_key=True, unique=True)
    role: int = Field(default=0)
    bank_seconds: int = Field(default=10)


class User(UserBase, table=True):
    accounts: List[ServiceAccount] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="user")
    posts: List["Post"] = Relationship(back_populates="user")

    def create(session: Session, user_init: UserBase, account_init: ServiceAccountBase = None):
        user = User.from_orm(user_init)
        session.add(user)
        if account_init:
            account_init.user_id = user.id
            account = ServiceAccount.from_orm(account_init)
            session.add(account)
            return (user, account)
        return (user, None)
    
    def get_from_account(session: Session, account_init: ServiceAccountBase = None):
        statement = select(User, ServiceAccount)\
            .where(ServiceAccount.service_id == account_init.service_id,
                   ServiceAccount.service_name == account_init.service_name,
                   User.id == ServiceAccount.user_id)
        data = session.exec(statement).first()
        if data is None: return (None, None)
        return data

    def is_can_analyse(self, audio_duration_s: int):
        if audio_duration_s < 0:
            raise ValueError(f"audio_duration_s must be greater than 0.")
        return self.bank_seconds >= audio_duration_s
    
    def substract_seconds(self, substract_s: int):
        if substract_s < 0:
            raise ValueError(f"substract_s must be greater than 0.")
        if not self.is_can_analyse(substract_s):
            raise ValueError(f"Can not substract. Value substract_s must be lower or equal than bank_seconds.")
        self.bank_seconds -= substract_s
    



class JobBase(SQLModel):
    audio_duration: float = Field()
    filehash: str = Field(index=True)
    model: str = Field(index=True)

    status: str = Field(default=task_states.PENDING)

    result: str | None = Field(default=None)


class Job(JobBase, table=True):
    id: UUID4 = Field(default_factory=uuid4, primary_key=True, unique=True)

    model_quality: int = Field()
    tasks: List["Task"] = Relationship(back_populates="job")

    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)
    startedAt: datetime | None = Field(default=None)
    endedAt: datetime | None = Field(default=None)

    def get_queue_position(self, session: Session):
        statement = select([func.count(Job.id)]).where(
            Job.createdAt < self.createdAt, Job.endedAt == None, Job.startedAt != None
        )
        return session.exec(statement).one()
    
    def is_started(self):
        return bool(self.startedAt)
    
    def is_processing(self):
        return bool(self.startedAt) and not bool(self.endedAt)
    
    def is_ended(self):
        return bool(self.endedAt)
    
    def is_ok(self):
        return self.status == task_states.SUCCESS if self.is_ended() else True


class TaskBase(SQLModel):
    status_webhook: HttpUrl | None = Field(default=None)
    file_webhook: HttpUrl = Field()
    user_id: UUID4 = Field(foreign_key="user.id")
    account_id: UUID4 = Field(foreign_key="service_account.id")
    job_id: UUID4 | None = Field(default=None)




class Task(TaskBase, table=True):
    id: UUID4 = Field(default_factory=uuid4, primary_key=True, unique=True)

    job_id: UUID4 = Field(foreign_key="job.id")

    job: Job = Relationship(back_populates="tasks")
    user: User = Relationship(back_populates="tasks")
    account: ServiceAccount = Relationship(back_populates="tasks")
    posts: List["Post"] = Relationship(back_populates="task")

    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)


    def create(session: Session, task_init: TaskBase, job_init: JobBase):
        statement = select(Job).where(
            Job.filehash == job_init.filehash, # same hash
            Job.model_quality >= WhisperModels.get_params(job_init.model) # better or like target model
        )
        exist_jobs = session.exec(statement).all()
        # Sorting by desc model quality
        exist_jobs = sorted(exist_jobs, key=lambda j: j.model_quality, reverse=True)

        inqueue_jobs = [j for j in exist_jobs if not j.startedAt]
        inprocess_jobs = [j for j in exist_jobs if j.startedAt and not j.endedAt]
        ready_jobs = [j for j in exist_jobs if j.endedAt]

        # Job at the lowest position in the queue
        best_inqueue_job = min(inqueue_jobs, key=lambda j: j.createdAt, default=None)
        # Job whith better model quality
        best_inprocess_job = max(inprocess_jobs, key=lambda j: j.model_quality, default=None)
        # Job whith better model quality
        best_ready_job = max(ready_jobs, key=lambda j: j.model_quality, default=None)

        job = None
        if best_ready_job: 
            job = best_ready_job
        elif best_inprocess_job: 
            job = best_inprocess_job
        elif best_inqueue_job: 
            job = best_inqueue_job
        

        task = Task.from_orm(task_init)

        if not job:
            job = Job(
                audio_duration=job_init.audio_duration,
                filehash=job_init.filehash,
                model=job_init.model,
                model_quality=WhisperModels.get_params(job_init.model)
            )
            session.add(job)
        
        task.job_id = job.id
        session.add(task)

        return (task, job)


class PostBase(SQLModel):
    type: str = Field(default="post")
    status: str = Field(default="visible")
    title: str|None = Field(default=None)
    content: str|None = Field(default=None)

    user_id: UUID4 = Field(foreign_key="user.id")
    task_id: UUID4 = Field(foreign_key="task.id")


class Post(PostBase, table=True):
    id: UUID4 = Field(default_factory=uuid4, primary_key=True, unique=True)

    title: str = Field()
    content: str = Field()

    user: User = Relationship(back_populates="posts")
    task: Task = Relationship(back_populates="posts")

    createdAt: datetime = Field(default_factory=datetime.now, nullable=False)
    updatedAt: datetime | None = Field(default=None, nullable=True)

    def create(session: Session, post_init: PostBase):
        task = session.get(Task, post_init.task_id)
        if task is None: raise ValueError(f"Task '{post_init.task_id}' not found!")
        job = task.job
        if not job.is_ended(): raise ValueError(f"Job '{job.id}' not ended!")
        if not job.is_ok(): raise ValueError(f"Job '{job.id}' ended with error, can not create post!")

        post = Post(
            title=short_uuid(task.id),
            content=result_stringify(TranscribeResult(**orjson.loads(job.result))),
            user_id=task.user_id,
            task_id=task.id
        )
        session.add(post)
        return post

    def set_content(self, new_content: str):
        self.content = new_content
        self.updatedAt = datetime.now()
