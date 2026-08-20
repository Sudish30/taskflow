from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.pagination import paginate


def create_task(db: Session, project_id: int, data: TaskCreate) -> Task:
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
) -> List[Task]:
    query = (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.id)
    )
    return paginate(query, limit=limit, offset=offset)


def get_task(db: Session, project_id: int, task_id: int) -> Optional[Task]:
    return (
        db.query(Task)
        .filter(Task.id == task_id, Task.project_id == project_id)
        .first()
    )


def update_task(db: Session, task: Task, data: TaskUpdate) -> Task:
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
