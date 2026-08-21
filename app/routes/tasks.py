from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.routes.auth import get_current_user
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services import project_service, task_service
from app.utils.pagination import MAX_LIMIT

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


def get_owned_project(project_id: int, db: Session, current_user: User) -> Project:
    """Return the project if it belongs to current_user, else raise 404."""
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
    """Create a new task inside a project."""
    get_owned_project(project_id, db, current_user)
    return task_service.create_task(db, project_id, data)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    project_id: int,
    limit: int = Query(default=20, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tasks for a project with pagination metadata.

    Returns an envelope: {items, total, limit, offset}.
    ``total`` is the count of all matching tasks, ignoring pagination.
    """
    get_owned_project(project_id, db, current_user)
    # Clamp limit to MAX_LIMIT to match pagination behaviour
    effective_limit = min(limit, MAX_LIMIT)
    items, total = task_service.get_tasks_for_project(
        db, project_id, limit=effective_limit, offset=offset
    )
    return TaskListResponse(
        items=items,
        total=total,
        limit=effective_limit,
        offset=offset,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a single task by ID."""
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
    """Update one or more fields on an existing task."""
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
    """Delete a task."""
    get_owned_project(project_id, db, current_user)
    task = task_service.get_task(db, project_id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    task_service.delete_task(db, task)
