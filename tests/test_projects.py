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


# --- Soft-delete and restore tests ---


def test_delete_project_is_soft_delete(auth_client, project):
    """Deleting a project soft-deletes it: 404 on get and absent from listing."""
    response = auth_client.delete(f"/projects/{project['id']}")
    assert response.status_code == 204
    # Confirm it's gone from normal get
    assert auth_client.get(f"/projects/{project['id']}").status_code == 404
    # Confirm it's gone from listing
    listing = auth_client.get("/projects").json()
    assert not any(p["id"] == project["id"] for p in listing)


def test_delete_already_soft_deleted_returns_404(auth_client, project):
    """Deleting a project that's already soft-deleted returns 404."""
    auth_client.delete(f"/projects/{project['id']}")
    response = auth_client.delete(f"/projects/{project['id']}")
    assert response.status_code == 404


def test_restore_project(auth_client, project):
    """Deleting then restoring a project makes it accessible again."""
    auth_client.delete(f"/projects/{project['id']}")
    response = auth_client.post(f"/projects/{project['id']}/restore")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == project["id"]
    assert body["name"] == "Inbox"
    # Confirm accessible again
    assert auth_client.get(f"/projects/{project['id']}").status_code == 200


def test_restore_active_project_returns_404(auth_client, project):
    """Restoring a project that is not soft-deleted returns 404."""
    response = auth_client.post(f"/projects/{project['id']}/restore")
    assert response.status_code == 404


def test_restore_nonexistent_project_returns_404(auth_client):
    """Restoring a project that doesn't exist returns 404."""
    response = auth_client.post("/projects/9999/restore")
    assert response.status_code == 404


def test_restore_other_users_project_returns_404(auth_client, project):
    """A user cannot restore another user's soft-deleted project."""
    auth_client.delete(f"/projects/{project['id']}")
    headers = second_user_headers(auth_client)
    response = auth_client.post(f"/projects/{project['id']}/restore", headers=headers)
    assert response.status_code == 404


def test_soft_deleted_project_tasks_inaccessible(auth_client, project):
    """Task endpoints return 404 for a soft-deleted project."""
    # Create a task first
    auth_client.post(f"/projects/{project['id']}/tasks", json={"title": "Task"})
    # Soft delete project
    auth_client.delete(f"/projects/{project['id']}")
    # Task endpoints should 404
    assert auth_client.get(f"/projects/{project['id']}/tasks").status_code == 404
    assert auth_client.post(
        f"/projects/{project['id']}/tasks", json={"title": "New"}
    ).status_code == 404


def test_restore_brings_back_tasks(auth_client, project):
    """Tasks survive the soft-delete/restore cycle and are accessible after restore."""
    task = auth_client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Task"}
    ).json()
    auth_client.delete(f"/projects/{project['id']}")
    auth_client.post(f"/projects/{project['id']}/restore")
    response = auth_client.get(f"/projects/{project['id']}/tasks")
    assert response.status_code == 200
    assert any(t["id"] == task["id"] for t in response.json())
