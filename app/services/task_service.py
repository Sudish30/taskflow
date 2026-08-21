from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.pagination import paginate


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
    status: Optional[TaskStatus] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None,
) -> List[Task]:
    """List a project's tasks in creation order, with optional filtering and limit/offset paging.

    Args:
        db: Database session.
        project_id: ID of the project whose tasks to list.
        limit: Maximum number of tasks to return.
        offset: Number of tasks to skip.
        status: If provided, only return tasks with this status.
        due_before: If provided, only return tasks with a due_date strictly before this datetime.
                    Tasks with no due_date are excluded.
        due_after: If provided, only return tasks with a due_date strictly after this datetime.
                   Tasks with no due_date are excluded.

    Returns:
        List of Task objects matching the filters.
    """
    query = (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.id)
    )

    if status is not None:
        query = query.filter(Task.status == status)
    if due_before is not None:
        query = query.filter(Task.due_date.isnot(None), Task.due_date < due_before)
    if due_after is not None:
        query = query.filter(Task.due_date.isnot(None), Task.due_date > due_after)

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
