"""Seed the local database with demo data.

Usage:
    python scripts/seed.py [--reset]

Creates a demo user (demo@example.com / demopassword) with a couple of
projects and tasks so the API has something to show right after setup.
"""

import argparse
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, SessionLocal, engine
from app.models.task import Task, TaskStatus
from app.models.project import Project
from app.services import auth_service

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demopassword"


def seed(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = auth_service.get_user_by_email(db, DEMO_EMAIL)
        if existing is not None:
            print(f"Demo user {DEMO_EMAIL} already exists, nothing to do.")
            print("Run with --reset to drop and recreate all tables.")
            return

        user = auth_service.create_user(db, DEMO_EMAIL, DEMO_PASSWORD)

        website = Project(
            name="Website redesign",
            description="Refresh the marketing site",
            owner_id=user.id,
        )
        backlog = Project(name="Backlog", owner_id=user.id)
        db.add_all([website, backlog])
        db.commit()
        db.refresh(website)
        db.refresh(backlog)

        now = datetime.utcnow()
        tasks = [
            Task(
                title="Draft new homepage copy",
                status=TaskStatus.in_progress,
                priority=2,
                due_date=now + timedelta(days=7),
                project_id=website.id,
            ),
            Task(
                title="Collect design feedback",
                status=TaskStatus.todo,
                priority=3,
                project_id=website.id,
            ),
            Task(
                title="Ship the new footer",
                status=TaskStatus.done,
                priority=4,
                project_id=website.id,
            ),
            Task(
                title="Investigate slow queries",
                status=TaskStatus.todo,
                priority=1,
                due_date=now + timedelta(days=2),
                project_id=backlog.id,
            ),
        ]
        db.add_all(tasks)
        db.commit()

        print(f"Seeded user {DEMO_EMAIL} (password: {DEMO_PASSWORD})")
        print(f"  - {website.name}: 3 tasks")
        print(f"  - {backlog.name}: 1 task")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables before seeding",
    )
    args = parser.parse_args()
    seed(reset=args.reset)
