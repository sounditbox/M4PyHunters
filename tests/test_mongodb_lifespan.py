from unittest.mock import AsyncMock, MagicMock

import pytest
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from starlette.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.mark.parametrize("failure", [None, "ping", "index", "close"])
def test_mongo_lifespan_closes_resources(monkeypatch, failure):
    engine = MagicMock()
    mongo = MagicMock()
    mongo.admin.command = AsyncMock()
    mongo.close = AsyncMock()
    ensure_indexes = AsyncMock()
    error = ConnectionFailure("connection lost")
    if failure == "ping":
        mongo.admin.command.side_effect = error
    elif failure == "index":
        ensure_indexes.side_effect = DuplicateKeyError("existing duplicates")
    elif failure == "close":
        mongo.close.side_effect = error
    monkeypatch.setattr("app.core.lifespan.create_database_engine", lambda _: engine)
    monkeypatch.setattr("app.core.lifespan.AsyncMongoClient", lambda *a, **kw: mongo)
    monkeypatch.setattr("app.core.lifespan.ensure_product_attribute_indexes", ensure_indexes)
    settings = Settings(
        _env_file=None, debug=False, secret_key="x" * 64,
        admin_password="admin-pass", user_password="user-pass",
        mongodb_url="mongodb://localhost:27017", mongodb_database="test_lifespan",
    )
    application = create_app(settings)

    def run():
        with TestClient(application):
            assert failure not in {"ping", "index"}
            assert application.state.mongo_database is mongo["test_lifespan"]

    if failure is None:
        run()
    else:
        with pytest.raises(DuplicateKeyError if failure == "index" else ConnectionFailure):
            run()
    mongo.admin.command.assert_awaited_once_with("ping")
    mongo.close.assert_awaited_once()
    engine.dispose.assert_called_once()


def test_mongo_disabled_at_startup(monkeypatch):
    engine = MagicMock()
    constructor = MagicMock()
    monkeypatch.setattr("app.core.lifespan.create_database_engine", lambda _: engine)
    monkeypatch.setattr("app.core.lifespan.AsyncMongoClient", constructor)
    settings = Settings(
        _env_file=None, debug=False, secret_key="x" * 64,
        admin_password="admin-pass", user_password="user-pass", mongodb_url=None,
    )
    with TestClient(create_app(settings)) as client:
        assert client.app.state.mongo_database is None
    constructor.assert_not_called()
    engine.dispose.assert_called_once()
