from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.pagination import paginate


def create_task(db: Session, project_id: int, data: TaskCreate) -> Task:
    """Create a task in the given project."""
    completed_at = datetime.utcnow() if data.status == TaskStatus.done else None
    task = Task(
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        due_date=data.due_date,
        project_id=project_id,
        completed_at=completed_at,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_tasks_for_project(
    db: Session, project_id: int, limit: int = None, offset: int = None
) -> List[Task]:
    """List a project's tasks in creation order, with limit/offset paging."""
    query = (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.id)
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

    # Manage completed_at based on status transitions
    if "status" in updates:
        if updates["status"] == TaskStatus.done:
            task.completed_at = datetime.utcnow()
        else:
            task.completed_at = None

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    """Delete a task."""
    db.delete(task)
    db.commit()
