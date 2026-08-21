"""
One-time migration: add index on tasks.project_id for faster task listing.

Usage:
    python -m scripts.add_task_project_id_index
"""
from sqlalchemy import text
from app.database import engine


def main():
    index_name = "ix_tasks_project_id"
    with engine.connect() as conn:
        # Works for both SQLite and PostgreSQL; IF NOT EXISTS prevents errors on re-runs.
        conn.execute(
            text(f"CREATE INDEX IF NOT EXISTS {index_name} ON tasks (project_id)")
        )
        conn.commit()
    print(f"Index '{index_name}' created (or already existed).")


if __name__ == "__main__":
    main()
