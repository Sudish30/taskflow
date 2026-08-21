from tests.conftest import register_and_login


def create_task(auth_client, project_id, **overrides):
    payload = {"title": "Write the report"}
    payload.update(overrides)
    return auth_client.post(f"/projects/{project_id}/tasks", json=payload)


def test_create_task_defaults(auth_client, project):
    response = create_task(auth_client, project["id"])
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Write the report"
    assert body["status"] == "todo"
    assert body["priority"] == 3
    assert body["due_date"] is None
    assert body["project_id"] == project["id"]


def test_create_task_with_all_fields(auth_client, project):
    response = create_task(
        auth_client,
        project["id"],
        title="Ship release",
        description="Cut the 1.0 tag",
        status="in_progress",
        priority=1,
        due_date="2026-12-31T17:00:00",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["priority"] == 1
    assert body["due_date"] == "2026-12-31T17:00:00"


def test_create_task_invalid_priority(auth_client, project):
    response = create_task(auth_client, project["id"], priority=10)
    assert response.status_code == 422


def test_create_task_invalid_status(auth_client, project):
    response = create_task(auth_client, project["id"], status="blocked")
    assert response.status_code == 422


def test_create_task_empty_title(auth_client, project):
    response = create_task(auth_client, project["id"], title="")
    assert response.status_code == 422


def test_create_task_project_not_found(auth_client):
    response = auth_client.post(
        "/projects/9999/tasks", json={"title": "Orphan"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_create_task_requires_auth(client):
    response = client.post("/projects/1/tasks", json={"title": "Nope"})
    assert response.status_code == 401


def test_create_task_on_other_users_project(auth_client, project):
    token = register_and_login(auth_client, "carol@example.com", "password456")
    response = auth_client.post(
        f"/projects/{project['id']}/tasks",
        json={"title": "Intruder"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_list_tasks_empty(auth_client, project):
    response = auth_client.get(f"/projects/{project['id']}/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_created(auth_client, project):
    create_task(auth_client, project["id"], title="First")
    create_task(auth_client, project["id"], title="Second")
    response = auth_client.get(f"/projects/{project['id']}/tasks")
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["First", "Second"]


def test_list_tasks_limit(auth_client, project):
    for i in range(5):
        create_task(auth_client, project["id"], title=f"Task {i}")
    response = auth_client.get(f"/projects/{project['id']}/tasks?limit=2")
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Task 0", "Task 1"]


def test_list_tasks_offset(auth_client, project):
    for i in range(5):
        create_task(auth_client, project["id"], title=f"Task {i}")
    response = auth_client.get(
        f"/projects/{project['id']}/tasks?limit=2&offset=3"
    )
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Task 3", "Task 4"]


def test_list_tasks_rejects_zero_limit(auth_client, project):
    response = auth_client.get(f"/projects/{project['id']}/tasks?limit=0")
    assert response.status_code == 422


def test_get_task(auth_client, project):
    created = create_task(auth_client, project["id"]).json()
    response = auth_client.get(
        f"/projects/{project['id']}/tasks/{created['id']}"
    )
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_task_not_found(auth_client, project):
    response = auth_client.get(f"/projects/{project['id']}/tasks/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_get_task_under_wrong_project(auth_client, project):
    other = auth_client.post("/projects", json={"name": "Other"}).json()
    created = create_task(auth_client, project["id"]).json()
    response = auth_client.get(f"/projects/{other['id']}/tasks/{created['id']}")
    assert response.status_code == 404


def test_update_task_status(auth_client, project):
    created = create_task(auth_client, project["id"]).json()
    response = auth_client.put(
        f"/projects/{project['id']}/tasks/{created['id']}",
        json={"status": "done"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert body["title"] == "Write the report"


def test_update_task_title_and_priority(auth_client, project):
    created = create_task(auth_client, project["id"]).json()
    response = auth_client.put(
        f"/projects/{project['id']}/tasks/{created['id']}",
        json={"title": "Updated title", "priority": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated title"
    assert body["priority"] == 5


def test_update_task_invalid_priority(auth_client, project):
    created = create_task(auth_client, project["id"]).json()
    response = auth_client.put(
        f"/projects/{project['id']}/tasks/{created['id']}",
        json={"priority": 0},
    )
    assert response.status_code == 422


def test_update_task_not_found(auth_client, project):
    response = auth_client.put(
        f"/projects/{project['id']}/tasks/9999", json={"title": "Ghost"}
    )
    assert response.status_code == 404


def test_delete_task(auth_client, project):
    created = create_task(auth_client, project["id"]).json()
    response = auth_client.delete(
        f"/projects/{project['id']}/tasks/{created['id']}"
    )
    assert response.status_code == 204
    follow_up = auth_client.get(
        f"/projects/{project['id']}/tasks/{created['id']}"
    )
    assert follow_up.status_code == 404


def test_delete_task_not_found(auth_client, project):
    response = auth_client.delete(f"/projects/{project['id']}/tasks/9999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Filter tests
# ---------------------------------------------------------------------------

def test_list_tasks_filter_by_status(auth_client, project):
    """Filtering by status returns only tasks with that status."""
    create_task(auth_client, project["id"], title="Todo task", status="todo")
    create_task(auth_client, project["id"], title="Done task", status="done")

    resp_todo = auth_client.get(f"/projects/{project['id']}/tasks?status=todo")
    assert resp_todo.status_code == 200
    todo_titles = [t["title"] for t in resp_todo.json()]
    assert todo_titles == ["Todo task"]

    resp_done = auth_client.get(f"/projects/{project['id']}/tasks?status=done")
    assert resp_done.status_code == 200
    done_titles = [t["title"] for t in resp_done.json()]
    assert done_titles == ["Done task"]

    resp_ip = auth_client.get(f"/projects/{project['id']}/tasks?status=in_progress")
    assert resp_ip.status_code == 200
    assert resp_ip.json() == []


def test_list_tasks_invalid_status_returns_422(auth_client, project):
    """An unrecognised status value must return 422."""
    response = auth_client.get(f"/projects/{project['id']}/tasks?status=blocked")
    assert response.status_code == 422


def test_list_tasks_filter_due_before(auth_client, project):
    """due_before returns only tasks whose due_date is strictly before the bound."""
    create_task(auth_client, project["id"], title="Early", due_date="2025-01-01T00:00:00")
    create_task(auth_client, project["id"], title="Late", due_date="2025-12-31T00:00:00")
    create_task(auth_client, project["id"], title="No date")

    response = auth_client.get(
        f"/projects/{project['id']}/tasks?due_before=2025-06-01T00:00:00"
    )
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Early"]
    assert "No date" not in titles


def test_list_tasks_filter_due_after(auth_client, project):
    """due_after returns only tasks whose due_date is strictly after the bound."""
    create_task(auth_client, project["id"], title="Early", due_date="2025-01-01T00:00:00")
    create_task(auth_client, project["id"], title="Late", due_date="2025-12-31T00:00:00")
    create_task(auth_client, project["id"], title="No date")

    response = auth_client.get(
        f"/projects/{project['id']}/tasks?due_after=2025-06-01T00:00:00"
    )
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Late"]
    assert "No date" not in titles


def test_list_tasks_no_due_date_excluded_when_bounds_set(auth_client, project):
    """Tasks with no due_date are excluded whenever any date bound is provided."""
    create_task(auth_client, project["id"], title="No date")

    resp_before = auth_client.get(
        f"/projects/{project['id']}/tasks?due_before=2099-01-01T00:00:00"
    )
    assert resp_before.status_code == 200
    assert resp_before.json() == []

    resp_after = auth_client.get(
        f"/projects/{project['id']}/tasks?due_after=2000-01-01T00:00:00"
    )
    assert resp_after.status_code == 200
    assert resp_after.json() == []


def test_list_tasks_filter_due_before_and_after(auth_client, project):
    """Combining due_before and due_after narrows the result to the window."""
    create_task(auth_client, project["id"], title="Jan", due_date="2025-01-01T00:00:00")
    create_task(auth_client, project["id"], title="Jun", due_date="2025-06-15T00:00:00")
    create_task(auth_client, project["id"], title="Dec", due_date="2025-12-31T00:00:00")

    response = auth_client.get(
        f"/projects/{project['id']}/tasks"
        "?due_after=2025-01-01T00:00:00&due_before=2025-12-31T00:00:00"
    )
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Jun"]


def test_list_tasks_filter_status_and_due_before(auth_client, project):
    """status and due_before combine with AND logic."""
    create_task(
        auth_client, project["id"],
        title="A", status="todo", due_date="2025-01-01T00:00:00",
    )
    create_task(
        auth_client, project["id"],
        title="B", status="done", due_date="2025-01-01T00:00:00",
    )
    create_task(
        auth_client, project["id"],
        title="C", status="todo", due_date="2025-12-31T00:00:00",
    )

    response = auth_client.get(
        f"/projects/{project['id']}/tasks?status=todo&due_before=2025-06-01T00:00:00"
    )
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["A"]


def test_list_tasks_filter_with_pagination(auth_client, project):
    """Filters compose correctly with limit/offset pagination."""
    for i in range(4):
        create_task(
            auth_client, project["id"],
            title=f"Task {i}",
            status="todo",
            due_date="2025-06-01T00:00:00",
        )

    response = auth_client.get(
        f"/projects/{project['id']}/tasks?status=todo&limit=2&offset=1"
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    titles = [t["title"] for t in body]
    assert titles == ["Task 1", "Task 2"]


def test_list_tasks_invalid_due_before_returns_422(auth_client, project):
    """An unparseable due_before value must return 422."""
    response = auth_client.get(
        f"/projects/{project['id']}/tasks?due_before=not-a-date"
    )
    assert response.status_code == 422


def test_list_tasks_invalid_due_after_returns_422(auth_client, project):
    """An unparseable due_after value must return 422."""
    response = auth_client.get(
        f"/projects/{project['id']}/tasks?due_after=not-a-date"
    )
    assert response.status_code == 422
