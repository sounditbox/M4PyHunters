import os

import pytest
from starlette.testclient import TestClient

from app.main import create_app

os.environ.update(
    DEBUG="false",
    SECRET_KEY="test-" + "x" * 64,
    ADMIN_PASSWORD="admin-pass",
    USER_PASSWORD="user-pass",
)


@pytest.fixture
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def admin_headers(client):
    response = client.post(
        "/auth/obtain_token",
        data={"username": "admin", "password": "admin-pass"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
