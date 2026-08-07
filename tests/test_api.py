import os
import sys

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("SQLALCHEMY_DATABASE_URL", "sqlite:///./test_whatsapp_notifier.db")

from main import app  # noqa: E402
from database import Base, engine  # noqa: E402

Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def auth_token():
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login(auth_token):
    assert auth_token

    login = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "secret123"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"


def test_duplicate_register_rejected(auth_token):
    duplicate = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "other@example.com", "password": "secret123"},
    )
    assert duplicate.status_code == 400


def test_protected_route_requires_auth():
    response = client.get("/contacts/")
    assert response.status_code == 401


def test_contact_crud(auth_token):
    headers = auth_headers(auth_token)

    create = client.post(
        "/contacts/",
        json={"name": "Alice", "phone_number": "+1111111111", "tags": "vip"},
        headers=headers,
    )
    assert create.status_code == 200
    contact_id = create.json()["id"]

    listing = client.get("/contacts/", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    update = client.put(
        f"/contacts/{contact_id}",
        json={"name": "Alice Updated", "phone_number": "+1111111111"},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["name"] == "Alice Updated"

    delete = client.delete(f"/contacts/{contact_id}", headers=headers)
    assert delete.status_code == 200


def test_template_crud(auth_token):
    headers = auth_headers(auth_token)

    create = client.post(
        "/templates/",
        json={"title": "Welcome", "body": "Hello {{name}}!"},
        headers=headers,
    )
    assert create.status_code == 200
    template_id = create.json()["id"]

    delete = client.delete(f"/templates/{template_id}", headers=headers)
    assert delete.status_code == 200


def test_group_create_and_delete(auth_token):
    headers = auth_headers(auth_token)

    create = client.post("/contacts/groups", json={"name": "Team A"}, headers=headers)
    assert create.status_code == 200
    group_id = create.json()["id"]

    delete = client.delete(f"/contacts/groups/{group_id}", headers=headers)
    assert delete.status_code == 200
