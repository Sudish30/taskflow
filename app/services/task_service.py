from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.pagination import paginate, paginate_with_count


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
    db: Session, project_id: int, limit: int = None, offset: int = None
) -> Dict:
    """List a project's tasks in creation order, with limit/offset paging.

    Returns a dict with keys: items, total, limit, offset.
    """
    query = (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.id)
    )
    items, total, limit, offset = paginate_with_count(query, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


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
