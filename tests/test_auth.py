import pytest


@pytest.mark.parametrize("path", ["/auth/me", "/products", "/products/1"])
def test_token_required(client, path):
    response = client.get(path)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize("username", ["admin", "unknown"])
def test_invalid_login(client, username):
    response = client.post(
        "/auth/token",
        data={"username": username, "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Неверные учётные данные"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_user_cannot_create_product(client):
    login = client.post(
        "/auth/token",
        data={"username": "user", "password": "user-pass"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    profile = client.get("/auth/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["role"] == "user"
    assert "hashed_password" not in profile.json()

    response = client.post(
        "/products",
        json={"name": "Gaming Mouse", "category": "electronics", "price": 49.9},
        headers=headers,
    )
    assert response.status_code == 403
