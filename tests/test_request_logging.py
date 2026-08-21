"""Tests for the request logging middleware."""

import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import create_app


# ── helpers ───────────────────────────────────────────────────────────────────


def make_test_client(request_log_enabled: bool) -> TestClient:
    """Build a fresh app + in-memory DB with the given request_log_enabled setting."""
    mock_settings = Settings(request_log_enabled=request_log_enabled)

    db_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=db_engine)
    TestingSessionLocal = sessionmaker(
        bind=db_engine, autocommit=False, autoflush=False
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    with patch("app.main.get_settings", return_value=mock_settings):
        application = create_app()

    application.dependency_overrides[get_db] = override_get_db
    return TestClient(application)


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def logging_client():
    """A TestClient whose app has request logging enabled (default)."""
    return make_test_client(request_log_enabled=True)


# ── tests ─────────────────────────────────────────────────────────────────────


def test_normal_request_is_logged(logging_client, caplog):
    """A regular POST request should produce exactly one log record."""
    with caplog.at_level(logging.INFO, logger="taskflow.requests"):
        response = logging_client.post(
            "/auth/register",
            json={"email": "log@example.com", "password": "password123"},
        )

    assert response.status_code == 201
    records = [r for r in caplog.records if r.name == "taskflow.requests"]
    assert len(records) == 1
    msg = records[0].getMessage()
    assert "POST" in msg
    assert "/auth/register" in msg
    assert "201" in msg


def test_health_path_not_logged(logging_client, caplog):
    """Requests to /health must not produce any log records."""
    with caplog.at_level(logging.INFO, logger="taskflow.requests"):
        response = logging_client.get("/health")

    assert response.status_code == 200
    records = [r for r in caplog.records if r.name == "taskflow.requests"]
    assert len(records) == 0


def test_log_line_contains_duration(logging_client, caplog):
    """The log message must include a duration expressed in milliseconds."""
    with caplog.at_level(logging.INFO, logger="taskflow.requests"):
        logging_client.post(
            "/auth/register",
            json={"email": "dur@example.com", "password": "password123"},
        )

    records = [r for r in caplog.records if r.name == "taskflow.requests"]
    assert len(records) == 1
    msg = records[0].getMessage()
    assert "ms" in msg


def test_logging_disabled_via_flag(caplog):
    """When request_log_enabled=False the middleware is not registered and nothing is logged."""
    disabled_client = make_test_client(request_log_enabled=False)

    with caplog.at_level(logging.INFO, logger="taskflow.requests"):
        disabled_client.post(
            "/auth/register",
            json={"email": "nolog@example.com", "password": "password123"},
        )

    records = [r for r in caplog.records if r.name == "taskflow.requests"]
    assert len(records) == 0


def test_authorization_header_not_logged(logging_client, caplog):
    """The Authorization header value must never appear in log output."""
    with caplog.at_level(logging.INFO, logger="taskflow.requests"):
        logging_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer supersecrettoken"},
        )

    records = [r for r in caplog.records if r.name == "taskflow.requests"]
    for record in records:
        msg = record.getMessage()
        assert "supersecrettoken" not in msg
        assert "Authorization" not in msg


def test_log_contains_method_path_status(logging_client, caplog):
    """The log line must contain the HTTP method, path, and numeric status code."""
    with caplog.at_level(logging.INFO, logger="taskflow.requests"):
        response = logging_client.get("/auth/me")  # 401 — no auth token

    assert response.status_code == 401
    records = [r for r in caplog.records if r.name == "taskflow.requests"]
    assert len(records) == 1
    msg = records[0].getMessage()
    assert "GET" in msg
    assert "/auth/me" in msg
    assert "401" in msg
