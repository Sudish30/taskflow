"""Tests for RequestLoggingMiddleware."""

import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.config import Settings, get_settings
from app.database import get_db
from app.main import create_app


def test_request_is_logged(client, caplog):
    """A normal request produces exactly one log record on taskflow.requests."""
    with caplog.at_level(logging.INFO, logger="taskflow.requests"):
        client.post(
            "/auth/register",
            json={"email": "log@example.com", "password": "password123"},
        )
    records = [r for r in caplog.records if r.name == "taskflow.requests"]
    assert len(records) == 1


def test_health_path_is_excluded(client, caplog):
    """GET /health must not produce any log records."""
    with caplog.at_level(logging.INFO, logger="taskflow.requests"):
        client.get("/health")
    records = [r for r in caplog.records if r.name == "taskflow.requests"]
    assert len(records) == 0


def test_log_contains_method_path_status_duration(client, caplog):
    """The log line must contain method, path, status code, and 'ms'."""
    with caplog.at_level(logging.INFO, logger="taskflow.requests"):
        client.post(
            "/auth/register",
            json={"email": "fmt@example.com", "password": "password123"},
        )
    records = [r for r in caplog.records if r.name == "taskflow.requests"]
    assert len(records) == 1
    msg = records[0].getMessage()
    assert "POST" in msg
    assert "/auth/register" in msg
    assert "201" in msg
    assert "ms" in msg


def test_authorization_header_not_logged(client, caplog):
    """Authorization header values must never appear in any log record."""
    with caplog.at_level(logging.INFO, logger="taskflow.requests"):
        client.get(
            "/auth/me",
            headers={"Authorization": "Bearer some-token"},
        )
    for record in caplog.records:
        msg = record.getMessage()
        assert "Authorization" not in msg
        assert "Bearer" not in msg
        # Also check raw args in case of lazy formatting
        if record.args:
            args_str = str(record.args)
            assert "Authorization" not in args_str
            assert "Bearer" not in args_str


def test_middleware_disabled_via_settings(monkeypatch, db_engine, caplog):
    """When request_log_enabled=False, no log records are emitted."""
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: Settings(request_log_enabled=False),
    )
    disabled_app = create_app()

    TestingSessionLocal = sessionmaker(
        bind=db_engine, autocommit=False, autoflush=False
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    disabled_app.dependency_overrides[get_db] = override_get_db

    with TestClient(disabled_app) as test_client:
        with caplog.at_level(logging.INFO, logger="taskflow.requests"):
            test_client.post(
                "/auth/register",
                json={"email": "disabled@example.com", "password": "password123"},
            )
    records = [r for r in caplog.records if r.name == "taskflow.requests"]
    assert len(records) == 0


def test_log_level_is_info(client, caplog):
    """Log records must be emitted at INFO level."""
    with caplog.at_level(logging.INFO, logger="taskflow.requests"):
        client.post(
            "/auth/register",
            json={"email": "level@example.com", "password": "password123"},
        )
    records = [r for r in caplog.records if r.name == "taskflow.requests"]
    assert len(records) >= 1
    assert records[0].levelname == "INFO"
