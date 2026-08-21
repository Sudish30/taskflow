"""
scripts/cleanup_orphaned_tasks.py

Delete tasks that reference a project_id that no longer exists.

Usage:
    python scripts/cleanup_orphaned_tasks.py [--dry-run]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.task import Task
from app.models.project import Project


def cleanup_orphaned_tasks(dry_run: bool = False) -> None:
    """Find and delete tasks whose project no longer exists.

    Args:
        dry_run: If True, print what would be deleted without making any changes.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        orphaned = (
            db.query(Task)
            .filter(
                ~db.query(Project.id)
                .filter(Project.id == Task.project_id)
                .exists()
            )
            .all()
        )

        count = len(orphaned)
        if count == 0:
            print("No orphaned tasks found.")
            return

        print(f"Found {count} orphaned task(s):")
        for task in orphaned:
            print(f"  - Task id={task.id} title={task.title!r} project_id={task.project_id}")

        if dry_run:
            print("Dry run: no changes made.")
        else:
            for task in orphaned:
                db.delete(task)
            db.commit()
            print(f"Deleted {count} orphaned task(s).")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove orphaned tasks")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be deleted without making changes",
    )
    args = parser.parse_args()
    cleanup_orphaned_tasks(dry_run=args.dry_run)
