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


# --- Sorting tests ---

def test_list_tasks_default_sort_is_created_at_asc(auth_client, project):
    create_task(auth_client, project["id"], title="First")
    create_task(auth_client, project["id"], title="Second")
    response = auth_client.get(f"/projects/{project['id']}/tasks")
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["First", "Second"]


def test_list_tasks_sort_created_at_desc(auth_client, project):
    create_task(auth_client, project["id"], title="First")
    create_task(auth_client, project["id"], title="Second")
    response = auth_client.get(
        f"/projects/{project['id']}/tasks?sort_by=created_at&order=desc"
    )
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Second", "First"]


def test_list_tasks_sort_by_priority_asc(auth_client, project):
    create_task(auth_client, project["id"], title="Low", priority=5)
    create_task(auth_client, project["id"], title="High", priority=1)
    create_task(auth_client, project["id"], title="Mid", priority=3)
    response = auth_client.get(
        f"/projects/{project['id']}/tasks?sort_by=priority&order=asc"
    )
    assert response.status_code == 200
    priorities = [t["priority"] for t in response.json()]
    assert priorities == [1, 3, 5]


def test_list_tasks_sort_by_priority_desc(auth_client, project):
    create_task(auth_client, project["id"], title="Low", priority=5)
    create_task(auth_client, project["id"], title="High", priority=1)
    create_task(auth_client, project["id"], title="Mid", priority=3)
    response = auth_client.get(
        f"/projects/{project['id']}/tasks?sort_by=priority&order=desc"
    )
    assert response.status_code == 200
    priorities = [t["priority"] for t in response.json()]
    assert priorities == [5, 3, 1]


def test_list_tasks_sort_by_due_date_asc(auth_client, project):
    create_task(auth_client, project["id"], title="Later", due_date="2026-12-01T00:00:00")
    create_task(auth_client, project["id"], title="Sooner", due_date="2026-01-01T00:00:00")
    response = auth_client.get(
        f"/projects/{project['id']}/tasks?sort_by=due_date&order=asc"
    )
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Sooner", "Later"]


def test_list_tasks_sort_by_due_date_desc(auth_client, project):
    create_task(auth_client, project["id"], title="Later", due_date="2026-12-01T00:00:00")
    create_task(auth_client, project["id"], title="Sooner", due_date="2026-01-01T00:00:00")
    response = auth_client.get(
        f"/projects/{project['id']}/tasks?sort_by=due_date&order=desc"
    )
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Later", "Sooner"]


def test_list_tasks_invalid_sort_by_returns_422(auth_client, project):
    response = auth_client.get(
        f"/projects/{project['id']}/tasks?sort_by=title"
    )
    assert response.status_code == 422


def test_list_tasks_invalid_order_returns_422(auth_client, project):
    response = auth_client.get(
        f"/projects/{project['id']}/tasks?order=random"
    )
    assert response.status_code == 422


def test_list_tasks_sort_composes_with_pagination(auth_client, project):
    for p in [5, 3, 1, 4, 2]:
        create_task(auth_client, project["id"], title=f"Task p{p}", priority=p)
    # Sort by priority asc, take second page (offset=2, limit=2) -> priorities 3, 4
    response = auth_client.get(
        f"/projects/{project['id']}/tasks?sort_by=priority&order=asc&limit=2&offset=2"
    )
    assert response.status_code == 200
    priorities = [t["priority"] for t in response.json()]
    assert priorities == [3, 4]
