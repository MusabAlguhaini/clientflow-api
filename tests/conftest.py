import os

# Use an isolated in-memory database for tests (must be set before importing the app).
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-bytes-long"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def register_and_login(client: TestClient, email: str = "alice@example.com") -> dict:
    client.post("/auth/register", json={"email": email, "full_name": "Test User", "password": "password123"})
    res = client.post("/auth/login", data={"username": email, "password": "password123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture()
def auth(client):
    return register_and_login(client)
