from sqlalchemy.orm import sessionmaker

from app.models.task import Task as TaskModel
from tests.conftest import register_and_login


def second_user_headers(client):
    token = register_and_login(client, "carol@example.com", "password456")
    return {"Authorization": f"Bearer {token}"}


def test_create_project(auth_client):
    response = auth_client.post(
        "/projects", json={"name": "Website", "description": "Marketing site"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Website"
    assert body["description"] == "Marketing site"
    assert "id" in body
    assert "created_at" in body


def test_create_project_requires_auth(client):
    response = client.post("/projects", json={"name": "Website"})
    assert response.status_code == 401


def test_create_project_missing_name(auth_client):
    response = auth_client.post("/projects", json={"description": "no name"})
    assert response.status_code == 422


def test_create_project_empty_name(auth_client):
    response = auth_client.post("/projects", json={"name": ""})
    assert response.status_code == 422


def test_list_projects_empty(auth_client):
    response = auth_client.get("/projects")
    assert response.status_code == 200
    assert response.json() == []


def test_list_projects_returns_created(auth_client):
    auth_client.post("/projects", json={"name": "One"})
    auth_client.post("/projects", json={"name": "Two"})
    response = auth_client.get("/projects")
    assert response.status_code == 200
    names = [p["name"] for p in response.json()]
    assert names == ["One", "Two"]


def test_list_projects_excludes_other_users(auth_client):
    auth_client.post("/projects", json={"name": "Mine"})
    headers = second_user_headers(auth_client)
    response = auth_client.get("/projects", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_project(auth_client, project):
    response = auth_client.get(f"/projects/{project['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Inbox"


def test_get_project_not_found(auth_client):
    response = auth_client.get("/projects/9999")
    assert response.status_code == 404
    assert response.json() == {"error": "Project not found"}


def test_get_other_users_project_hidden(auth_client, project):
    headers = second_user_headers(auth_client)
    response = auth_client.get(f"/projects/{project['id']}", headers=headers)
    assert response.status_code == 404


def test_update_project_name(auth_client, project):
    response = auth_client.put(
        f"/projects/{project['id']}", json={"name": "Renamed"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed"
    assert body["description"] == "Default project"


def test_update_project_description_only(auth_client, project):
    response = auth_client.put(
        f"/projects/{project['id']}", json={"description": "New description"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Inbox"
    assert body["description"] == "New description"


def test_update_project_not_found(auth_client):
    response = auth_client.put("/projects/9999", json={"name": "Nope"})
    assert response.status_code == 404
    assert response.json() == {"error": "Project not found"}


def test_delete_project(auth_client, project):
    response = auth_client.delete(f"/projects/{project['id']}")
    assert response.status_code == 204
    follow_up = auth_client.get(f"/projects/{project['id']}")
    assert follow_up.status_code == 404


def test_delete_project_not_found(auth_client):
    response = auth_client.delete("/projects/9999")
    assert response.status_code == 404


def test_delete_project_cascades_to_tasks(auth_client, project):
    """Deleting a project via the API should remove all its tasks."""
    # Create two tasks under the project
    auth_client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Task A"}
    )
    auth_client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Task B"}
    )
    # Verify tasks exist before deletion
    tasks_before = auth_client.get(f"/projects/{project['id']}/tasks")
    assert tasks_before.status_code == 200
    assert len(tasks_before.json()) == 2

    # Delete the project
    delete_response = auth_client.delete(f"/projects/{project['id']}")
    assert delete_response.status_code == 204

    # Verify the project is gone
    get_response = auth_client.get(f"/projects/{project['id']}")
    assert get_response.status_code == 404


def test_delete_project_removes_tasks_from_db(client, db_engine):
    """Verify at the DB level that task rows are deleted when a project is deleted."""
    token = register_and_login(client, "dbcheck@example.com", "password123")
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj = client.post("/projects", json={"name": "ToDelete"}, headers=headers).json()
    project_id = proj["id"]

    # Create tasks
    client.post(f"/projects/{project_id}/tasks", json={"title": "T1"}, headers=headers)
    client.post(f"/projects/{project_id}/tasks", json={"title": "T2"}, headers=headers)

    # Delete project via API
    resp = client.delete(f"/projects/{project_id}", headers=headers)
    assert resp.status_code == 204

    # Verify no task rows remain in the database
    TestingSession = sessionmaker(bind=db_engine)
    db = TestingSession()
    try:
        remaining = db.query(TaskModel).filter(TaskModel.project_id == project_id).all()
        assert remaining == [], f"Expected no tasks, found {len(remaining)}"
    finally:
        db.close()
