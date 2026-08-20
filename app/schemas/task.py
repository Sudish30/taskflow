from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskStatus
from app.utils.validators import validate_priority


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.todo
    priority: int = 3
    due_date: Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def check_priority(cls, value: int) -> int:
        return validate_priority(value)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = None
    due_date: Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def check_priority(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        return validate_priority(value)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: int
    due_date: Optional[datetime]
    project_id: int
    created_at: datetime
