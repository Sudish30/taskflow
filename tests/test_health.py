from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


def test_health_ok(client):
    """Health endpoint returns 200 with ok status when DB is reachable."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_health_db_error():
    """Health endpoint returns 503 with degraded status when DB query fails."""
    # Create a mock session whose execute() raises OperationalError
    mock_db = MagicMock()
    mock_db.execute.side_effect = OperationalError(
        "SELECT 1", params={}, orig=Exception("connection refused")
    )

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        test_client = TestClient(app, raise_server_exceptions=False)
        response = test_client.get("/health")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "degraded"
        assert body["database"] == "error"
    finally:
        app.dependency_overrides.clear()
