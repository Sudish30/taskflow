# TaskFlow

A task-management REST API built with FastAPI and SQLAlchemy. Users register and
log in with a JWT token, create projects, and manage tasks within each project.

## Features

- Token-based auth (register, login, current user)
- Project CRUD, scoped to the authenticated user
- Task CRUD nested under projects, with status (`todo` / `in_progress` / `done`),
  priority (1–5), and optional due dates
- Limit/offset pagination on task listings
- SQLite storage — no external services needed

## Setup

Requires Python 3.11.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the API

```bash
uvicorn app.main:app --reload
```

Interactive docs at http://127.0.0.1:8000/docs.

Configuration is read from environment variables prefixed with `TASKFLOW_`
(e.g. `TASKFLOW_SECRET_KEY`, `TASKFLOW_DATABASE_URL`). Everything has a working
default, so no configuration is required for local development.

## Running the tests

```bash
python -m pytest -v
```

Tests use an in-memory SQLite database per test, so they need no setup and leave
nothing behind.

## Project layout

```
app/
  main.py        # app factory and router registration
  config.py      # settings via pydantic-settings
  database.py    # engine, session, get_db dependency
  models/        # SQLAlchemy models (User, Project, Task)
  schemas/       # pydantic request/response schemas
  routes/        # HTTP layer (auth, projects, tasks)
  services/      # business logic
  utils/         # validators, pagination helper
tests/
```
