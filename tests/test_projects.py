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


# --- Archive feature tests ---


def test_create_project_has_is_archived_field(auth_client):
    response = auth_client.post("/projects", json={"name": "Test"})
    assert response.status_code == 201
    assert response.json()["is_archived"] is False


def test_archive_project_hides_from_default_list(auth_client, project):
    response = auth_client.patch(
        f"/projects/{project['id']}/archive", json={"is_archived": True}
    )
    assert response.status_code == 200
    assert response.json()["is_archived"] is True

    list_response = auth_client.get("/projects")
    ids = [p["id"] for p in list_response.json()]
    assert project["id"] not in ids


def test_archived_projects_appear_in_archived_list(auth_client, project):
    auth_client.patch(
        f"/projects/{project['id']}/archive", json={"is_archived": True}
    )
    response = auth_client.get("/projects?archived=true")
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()]
    assert project["id"] in ids


def test_default_list_excludes_archived(auth_client):
    r1 = auth_client.post("/projects", json={"name": "Active"}).json()
    r2 = auth_client.post("/projects", json={"name": "Old Finished"}).json()
    auth_client.patch(f"/projects/{r2['id']}/archive", json={"is_archived": True})

    response = auth_client.get("/projects")
    ids = [p["id"] for p in response.json()]
    assert r1["id"] in ids
    assert r2["id"] not in ids


def test_unarchive_project_restores_to_default_list(auth_client, project):
    auth_client.patch(
        f"/projects/{project['id']}/archive", json={"is_archived": True}
    )
    auth_client.patch(
        f"/projects/{project['id']}/archive", json={"is_archived": False}
    )
    response = auth_client.get("/projects")
    ids = [p["id"] for p in response.json()]
    assert project["id"] in ids


def test_archive_project_not_found(auth_client):
    response = auth_client.patch("/projects/9999/archive", json={"is_archived": True})
    assert response.status_code == 404
    assert response.json() == {"error": "Project not found"}


def test_archived_list_excludes_active_projects(auth_client, project):
    response = auth_client.get("/projects?archived=true")
    ids = [p["id"] for p in response.json()]
    assert project["id"] not in ids
