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
(e.g. `TASKFLOW_SECRET_KEY`, `TASKFLOW_DATABASE_URL`); see `.env.example` for
the full list. Everything has a working default, so no configuration is
required for local development.

To populate the database with demo data:

```bash
python scripts/seed.py            # creates demo@example.com / demopassword
python scripts/seed.py --reset    # drop all tables first
```

## API reference

All `/projects` routes require an `Authorization: Bearer <token>` header.

| Method | Path | Description |
|--------|------|-------------|
| POST   | `/auth/register` | Create an account |
| POST   | `/auth/login` | Get an access token |
| GET    | `/auth/me` | Current user |
| POST   | `/projects` | Create a project |
| GET    | `/projects` | List your projects |
| GET    | `/projects/{id}` | Get one project |
| PUT    | `/projects/{id}` | Update a project |
| DELETE | `/projects/{id}` | Delete a project |
| POST   | `/projects/{id}/tasks` | Create a task |
| GET    | `/projects/{id}/tasks?limit=&offset=` | List tasks (paginated) |
| GET    | `/projects/{id}/tasks/{task_id}` | Get one task |
| PUT    | `/projects/{id}/tasks/{task_id}` | Update a task |
| DELETE | `/projects/{id}/tasks/{task_id}` | Delete a task |
| GET    | `/health` | Liveness check |

Example session:

```bash
curl -s -X POST localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email": "me@example.com", "password": "password123"}'

TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "me@example.com", "password": "password123"}' | jq -r .access_token)

curl -s -X POST localhost:8000/projects \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name": "My project"}'

curl -s -X POST localhost:8000/projects/1/tasks \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title": "First task", "priority": 2, "due_date": "2026-09-01T09:00:00"}'
```

Task `status` is one of `todo`, `in_progress`, `done`; `priority` runs 1
(highest) to 5 (lowest).

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
