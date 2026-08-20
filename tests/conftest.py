import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

USER_EMAIL = "alice@example.com"
USER_PASSWORD = "supersecret1"


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def client(db_engine):
    TestingSessionLocal = sessionmaker(
        bind=db_engine, autocommit=False, autoflush=False
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def register_and_login(client, email, password):
    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    return response.json()["access_token"]


@pytest.fixture()
def auth_client(client):
    token = register_and_login(client, USER_EMAIL, USER_PASSWORD)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture()
def project(auth_client):
    response = auth_client.post(
        "/projects", json={"name": "Inbox", "description": "Default project"}
    )
    return response.json()
