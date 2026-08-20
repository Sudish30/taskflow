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
    """List all projects owned by a user, oldest first."""
    return (
        db.query(Project)
        .filter(Project.owner_id == owner_id)
        .order_by(Project.id)
        .all()
    )


def get_project(db: Session, owner_id: int, project_id: int) -> Optional[Project]:
    """Fetch a project by id, scoped to its owner. None if missing."""
    return (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == owner_id)
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
    """Delete a project."""
    db.delete(project)
    db.commit()
