"""One-time migration: delete tasks whose project no longer exists.

Usage:
    python scripts/migrate_cascade.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import exists, select

from app.database import SessionLocal, engine, Base
from app.models.project import Project  # noqa: F401 — ensure model is registered
from app.models.task import Task


def cleanup_orphaned_tasks() -> None:
    """Delete all Task rows whose project_id references a non-existent project.

    This is safe to run multiple times — on subsequent runs it will find
    zero orphans and report 0 deletions.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        orphaned = (
            db.query(Task)
            .filter(
                ~exists(select(Project.id).where(Project.id == Task.project_id))
            )
            .all()
        )
        count = len(orphaned)
        for task in orphaned:
            db.delete(task)
        db.commit()
        print(f"Deleted {count} orphaned task(s).")
    finally:
        db.close()


if __name__ == "__main__":
    cleanup_orphaned_tasks()
