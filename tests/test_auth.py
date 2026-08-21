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


# ---------------------------------------------------------------------------
# New tests for strengthened password requirements (Issue #7)
# ---------------------------------------------------------------------------

def test_register_password_no_digit(client):
    """A password with letters but no digit should be rejected with a
    message mentioning 'digit'."""
    response = client.post(
        "/auth/register",
        json={"email": "nodigit@example.com", "password": "aaaaaaaa"},
    )
    assert response.status_code == 422
    detail_str = str(response.json()["detail"])
    assert "digit" in detail_str


def test_register_password_no_letter(client):
    """A password with digits but no letter should be rejected with a
    message mentioning 'letter'."""
    response = client.post(
        "/auth/register",
        json={"email": "noletter@example.com", "password": "12345678"},
    )
    assert response.status_code == 422
    detail_str = str(response.json()["detail"])
    assert "letter" in detail_str


def test_register_password_too_long(client):
    """A password exceeding 72 characters should be rejected with a
    message mentioning '72'."""
    response = client.post(
        "/auth/register",
        json={"email": "toolong@example.com", "password": "Aa1" + "x" * 70},
    )
    assert response.status_code == 422
    detail_str = str(response.json()["detail"])
    assert "72" in detail_str


def test_register_password_exactly_max_length(client):
    """A password of exactly 72 characters (the maximum) must be accepted."""
    # "Aa1" (3 chars) + 69 "x"s = 72 chars total
    response = client.post(
        "/auth/register",
        json={"email": "maxlen@example.com", "password": "Aa1" + "x" * 69},
    )
    assert response.status_code == 201


def test_register_short_password_error_message(client):
    """The too-short error message must mention the minimum length (8)."""
    response = client.post(
        "/auth/register",
        json={"email": "short2@example.com", "password": "Ab1"},
    )
    assert response.status_code == 422
    detail_str = str(response.json()["detail"])
    assert "8" in detail_str


def test_login_does_not_validate_password_strength(client):
    """The login endpoint must not enforce password-complexity rules.
    Submitting a weak password should yield 401 (bad credentials), not 422."""
    response = client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "aaaaaaaa"},
    )
    # Authentication failure, not a validation error
    assert response.status_code == 401
