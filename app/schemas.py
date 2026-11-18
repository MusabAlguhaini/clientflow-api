from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import TaskPriority, TaskStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Auth / users ----
class UserCreate(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", examples=["you@example.com"])
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class UserOut(ORMModel):
    id: int
    email: str
    full_name: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Clients ----
class ClientBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=160)
    notes: str | None = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    email: str | None = None
    company: str | None = None
    notes: str | None = None


class ClientOut(ORMModel, ClientBase):
    id: int
    created_at: datetime


# ---- Tasks ----
class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None


class TaskOut(ORMModel, TaskBase):
    id: int
    client_id: int
    created_at: datetime


class Summary(BaseModel):
    clients: int
    tasks_total: int
    tasks_by_status: dict[str, int]
    overdue_tasks: int
