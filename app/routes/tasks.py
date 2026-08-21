from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.task import TaskStatus
from app.models.user import User
from app.routes.auth import get_current_user
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services import project_service, task_service

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


def get_owned_project(project_id: int, db: Session, current_user: User) -> Project:
    """Fetch a project owned by the current user, raising 404 if not found."""
    project = project_service.get_project(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: int,
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_project(project_id, db, current_user)
    return task_service.create_task(db, project_id, data)


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    project_id: int,
    limit: int = Query(default=20, ge=1),
    offset: int = Query(default=0, ge=0),
    status: Optional[TaskStatus] = Query(default=None),
    due_before: Optional[datetime] = Query(default=None),
    due_after: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tasks for a project with optional filtering by status and due date.

    Args:
        project_id: ID of the project.
        limit: Maximum number of tasks to return (default 20, min 1).
        offset: Number of tasks to skip (default 0).
        status: Filter by task status (todo, in_progress, done). Returns 422 for invalid values.
        due_before: Only return tasks with due_date before this ISO datetime. Excludes tasks with no due date.
        due_after: Only return tasks with due_date after this ISO datetime. Excludes tasks with no due date.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        List of matching tasks.
    """
    get_owned_project(project_id, db, current_user)
    return task_service.get_tasks_for_project(
        db,
        project_id,
        limit=limit,
        offset=offset,
        status=status,
        due_before=due_before,
        due_after=due_after,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_project(project_id, db, current_user)
    task = task_service.get_task(db, project_id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    project_id: int,
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_project(project_id, db, current_user)
    task = task_service.get_task(db, project_id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task_service.update_task(db, task, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_project(project_id, db, current_user)
    task = task_service.get_task(db, project_id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    task_service.delete_task(db, task)
