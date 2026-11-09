from datetime import datetime, timezone

import jwt
import pytest
from sqlalchemy.engine import make_url
from starlette.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.mark.parametrize("use_default_settings", [False, True])
def test_app_settings_are_used_and_isolated(
    tmp_path, monkeypatch, use_default_settings, migrate_database,
):
    settings = [
        Settings(
            _env_file=None,
            app_name=f"Test app {index}",
            debug=True,
            database_url=f"sqlite+pysqlite:///{tmp_path / f'app-{index}.db'}",
            mongodb_url=None,
            secret_key=key * 64,
            admin_password=f"admin-pass-{index}",
            user_password=f"user-pass-{index}",
            access_token_expire_minutes=minutes,
        )
        for index, (key, minutes) in enumerate([("a", 7), ("b", 13)])
    ]
    for config in settings:
        migrate_database(config.database_url)
    monkeypatch.setattr("app.main.get_settings", lambda: settings[0])
    first_app = create_app() if use_default_settings else create_app(settings[0])
    second_app = create_app(settings[1])

    with TestClient(first_app) as first, TestClient(second_app) as second:
        clients = [first, second]
        tokens = []
        for client, config in zip(clients, settings):
            assert client.app.title == config.app_name
            assert client.app.debug == config.debug
            assert client.app.state.engine.url == make_url(config.database_url)
            response = client.post(
                "/auth/obtain_token",
                data={
                    "username": "admin",
                    "password": config.admin_password.get_secret_value(),
                },
            )
            assert response.status_code == 200
            token = response.json()["access_token"]
            tokens.append(token)
            payload = jwt.decode(
                token, config.secret_key.get_secret_value(), algorithms=["HS256"],
            )
            assert payload["sub"] == "admin"
            remaining = payload["exp"] - datetime.now(timezone.utc).timestamp()
            lifetime = config.access_token_expire_minutes * 60
            assert lifetime - 10 <= remaining <= lifetime

        for index, client in enumerate(clients):
            own_headers = {"Authorization": f"Bearer {tokens[index]}"}
            other_headers = {"Authorization": f"Bearer {tokens[1 - index]}"}
            assert client.get("/auth/me", headers=own_headers).status_code == 200
            assert client.get("/auth/me", headers=other_headers).status_code == 401
