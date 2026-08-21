from tests.conftest import USER_EMAIL, USER_PASSWORD, register_and_login


def test_register_returns_created_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "id" in body
    assert "created_at" in body


def test_register_response_excludes_password(client):
    response = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    body = response.json()
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "password123"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"


def test_register_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "password123"},
    )
    assert response.status_code == 422


def test_register_short_password(client):
    response = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "abc"},
    )
    assert response.status_code == 422


def test_register_normalizes_email_case(client):
    response = client.post(
        "/auth/register",
        json={"email": "MixedCase@Example.com", "password": "password123"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "mixedcase@example.com"


def test_login_returns_token(client):
    client.post(
        "/auth/register",
        json={"email": USER_EMAIL, "password": USER_PASSWORD},
    )
    response = client.post(
        "/auth/login",
        json={"email": USER_EMAIL, "password": USER_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"email": USER_EMAIL, "password": USER_PASSWORD},
    )
    response = client.post(
        "/auth/login",
        json={"email": USER_EMAIL, "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email(client):
    response = client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )
    assert response.status_code == 401


def test_me_returns_current_user(auth_client):
    response = auth_client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == USER_EMAIL


def test_me_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_with_invalid_token(client):
    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_token_from_login_works_on_protected_route(client):
    token = register_and_login(client, "bob@example.com", "password123")
    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "bob@example.com"


def test_login_with_mixed_case_email_succeeds(client):
    """Registering with mixed-case email and logging in with the same casing should succeed."""
    # Registration normalizes the email to lowercase
    client.post(
        "/auth/register",
        json={"email": "Alice@Example.com", "password": "password123"},
    )
    # Login with the same mixed-case email should succeed
    response = client.post(
        "/auth/login",
        json={"email": "Alice@Example.com", "password": "password123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_login_normalizes_email_case(client):
    """Login should succeed regardless of the email casing supplied by the user."""
    # Register with lowercase email
    client.post(
        "/auth/register",
        json={"email": "bob@example.com", "password": "password123"},
    )
    # Login with uppercase version should also succeed
    response = client.post(
        "/auth/login",
        json={"email": "BOB@EXAMPLE.COM", "password": "password123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
