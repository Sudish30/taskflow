from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, owner_id: int, data: ProjectCreate) -> Project:
    """Create a project owned by the given user."""
    project = Project(
        name=data.name,
        description=data.description,
        owner_id=owner_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_projects_for_user(db: Session, owner_id: int) -> List[Project]:
    """List all active (non-deleted) projects owned by a user, oldest first."""
    return (
        db.query(Project)
        .filter(Project.owner_id == owner_id, Project.deleted_at == None)
        .order_by(Project.id)
        .all()
    )


def get_project(db: Session, owner_id: int, project_id: int) -> Optional[Project]:
    """Fetch an active project by id, scoped to its owner. None if missing or soft-deleted."""
    return (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == owner_id,
            Project.deleted_at == None,
        )
        .first()
    )


def get_deleted_project(db: Session, owner_id: int, project_id: int) -> Optional[Project]:
    """Fetch a soft-deleted project by id, scoped to owner. None if not soft-deleted or missing."""
    return (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == owner_id,
            Project.deleted_at != None,
        )
        .first()
    )


def update_project(db: Session, project: Project, data: ProjectUpdate) -> Project:
    """Apply the fields present in the update payload to a project."""
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project) -> None:
    """Soft-delete a project by setting deleted_at."""
    project.deleted_at = datetime.utcnow()
    db.commit()


def restore_project(db: Session, project: Project) -> Project:
    """Restore a soft-deleted project by clearing deleted_at."""
    project.deleted_at = None
    db.commit()
    db.refresh(project)
    return project
