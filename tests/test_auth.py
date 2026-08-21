import time

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
# Rate-limiting tests
# ---------------------------------------------------------------------------


def _make_failed_attempts(client, email: str, n: int) -> None:
    """POST n failed login attempts for *email* using a wrong password."""
    for _ in range(n):
        resp = client.post(
            "/auth/login",
            json={"email": email, "password": "definitely-wrong-password"},
        )
        # Each attempt before the limit is hit must be 401
        assert resp.status_code == 401


def test_rate_limit_triggers_after_5_failures(client):
    """The 6th consecutive failure for the same email must return 429."""
    email = "victim@example.com"
    client.post("/auth/register", json={"email": email, "password": "password123"})

    _make_failed_attempts(client, email, 5)

    response = client.post(
        "/auth/login",
        json={"email": email, "password": "wrong-again"},
    )
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert int(response.headers["Retry-After"]) > 0


def test_rate_limit_response_body(client):
    """The 429 response body must contain a descriptive detail message."""
    email = "victim2@example.com"
    client.post("/auth/register", json={"email": email, "password": "password123"})

    _make_failed_attempts(client, email, 5)

    response = client.post(
        "/auth/login",
        json={"email": email, "password": "wrong-again"},
    )
    assert response.status_code == 429
    assert "Too many" in response.json()["detail"]


def test_rate_limit_applies_to_unknown_email(client):
    """Rate limiting must apply even when the email is not registered.

    This ensures the limiter does not leak whether an account exists.
    """
    email = "ghost@example.com"  # never registered

    _make_failed_attempts(client, email, 5)

    response = client.post(
        "/auth/login",
        json={"email": email, "password": "wrong-again"},
    )
    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_rate_limit_reset_on_success(client):
    """A successful login resets the failure counter.

    After a successful login, 5 more failed attempts should all return 401,
    not 429 — the window was reset.
    """
    email = "resetter@example.com"
    password = "password123"
    client.post("/auth/register", json={"email": email, "password": password})

    # 4 failures — not yet blocked
    for _ in range(4):
        resp = client.post(
            "/auth/login",
            json={"email": email, "password": "wrong"},
        )
        assert resp.status_code == 401

    # Successful login — resets the counter
    ok = client.post("/auth/login", json={"email": email, "password": password})
    assert ok.status_code == 200

    # 5 more failures — counter was reset so all should be 401, not 429
    for _ in range(5):
        resp = client.post(
            "/auth/login",
            json={"email": email, "password": "wrong"},
        )
        assert resp.status_code == 401


def test_rate_limit_correct_credentials_not_blocked_by_prior_failures(client):
    """Correct credentials succeed even after 4 prior failures (not yet blocked)."""
    email = "almost@example.com"
    password = "password123"
    client.post("/auth/register", json={"email": email, "password": password})

    # 4 failures (one below the threshold)
    for _ in range(4):
        resp = client.post(
            "/auth/login",
            json={"email": email, "password": "wrong"},
        )
        assert resp.status_code == 401

    # Correct credentials on the 5th attempt — must still succeed
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_rate_limit_retry_after_header_is_integer_string(client):
    """The Retry-After header must be a parseable integer between 1 and 60."""
    email = "header-check@example.com"
    client.post("/auth/register", json={"email": email, "password": "password123"})

    _make_failed_attempts(client, email, 5)

    response = client.post(
        "/auth/login",
        json={"email": email, "password": "wrong-again"},
    )
    assert response.status_code == 429
    retry_after_str = response.headers["Retry-After"]
    retry_after = int(retry_after_str)  # must not raise
    assert 1 <= retry_after <= 61  # window is 60 s; +1 ceiling; allow small drift
