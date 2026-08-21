from unittest.mock import MagicMock

from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


def test_health_returns_ok_when_db_is_reachable(client):
    """Happy path: DB is up, expect 200 with status and database both ok."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_health_returns_503_when_db_is_unreachable(client):
    """Sad path: DB query raises, expect 503 with degraded status."""

    def broken_db():
        db = MagicMock()
        db.execute.side_effect = OperationalError(
            "connection refused", params=None, orig=None
        )
        yield db

    app.dependency_overrides[get_db] = broken_db
    try:
        response = client.get("/health")
    finally:
        # Remove the broken override; conftest teardown will clear the rest
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"] == "error"
