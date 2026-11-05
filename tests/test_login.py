def test_login(client):
    response = client.post(
        "/auth/obtain_token",
        data={"username": "admin", "password": "admin-pass"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
