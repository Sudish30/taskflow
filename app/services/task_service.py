from typing import List, Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.pagination import paginate

SORT_COLUMN_MAP = {
    "created_at": Task.created_at,
    "due_date": Task.due_date,
    "priority": Task.priority,
}


def create_task(db: Session, project_id: int, data: TaskCreate) -> Task:
    """Create a task in the given project."""
    task = Task(
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        due_date=data.due_date,
        project_id=project_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_tasks_for_project(
    db: Session,
    project_id: int,
    limit: int = None,
    offset: int = None,
    sort_by: str = "created_at",
    order: str = "asc",
) -> List[Task]:
    """List a project's tasks with sorting and limit/offset paging."""
    sort_column = SORT_COLUMN_MAP[sort_by]
    order_func = asc if order == "asc" else desc
    query = (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(order_func(sort_column))
    )
    return paginate(query, limit=limit, offset=offset)


def get_task(db: Session, project_id: int, task_id: int) -> Optional[Task]:
    """Fetch a task by id, scoped to its project. None if missing."""
    return (
        db.query(Task)
        .filter(Task.id == task_id, Task.project_id == project_id)
        .first()
    )


def update_task(db: Session, task: Task, data: TaskUpdate) -> Task:
    """Apply the fields present in the update payload to a task."""
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    """Delete a task."""
    db.delete(task)
    db.commit()
