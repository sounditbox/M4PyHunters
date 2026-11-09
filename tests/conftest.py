import os
from pathlib import Path
from uuid import uuid4

import pytest

os.environ.update(
    DEBUG="false",
    SECRET_KEY="test-" + "x" * 64,
    ADMIN_PASSWORD="admin-pass",
    USER_PASSWORD="user-pass",
)

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from starlette.testclient import TestClient
from sqlmodel import Session

from app.core.config import Settings
from app.db.database import create_database_engine
from app.main import create_app
from app.models import Product


@pytest.fixture
def migrate_database():
    def migrate(database_url, revision="head"):
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        config.attributes["database_url"] = database_url
        command.upgrade(config, revision)
        return config

    return migrate


@pytest.fixture
def database_url(tmp_path):
    """Use an isolated SQLite file or a unique schema in TEST_DATABASE_URL."""
    postgres_url = os.getenv("TEST_DATABASE_URL")
    if not postgres_url:
        yield f"sqlite+pysqlite:///{tmp_path / 'test.db'}"
        return

    url = make_url(postgres_url)
    if url.get_backend_name() != "postgresql":
        raise ValueError("TEST_DATABASE_URL must point to PostgreSQL")
    schema = f"test_{uuid4().hex}"
    engine = create_database_engine(postgres_url)
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
        yield url.update_query_dict(
            {"options": f"-csearch_path={schema}"},
        ).render_as_string(hide_password=False)
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        engine.dispose()


@pytest.fixture
def mongo_settings():
    return {
        "mongodb_url": os.getenv(
            "TEST_MONGODB_URL",
            "mongodb://mongo:mongo@127.0.0.1:27017/?authSource=admin",
        ),
        "mongodb_database": f"test_{uuid4().hex}",
    }


@pytest.fixture
def client(database_url, migrate_database, mongo_settings):
    migrate_database(database_url)
    settings = Settings(
        _env_file=None,
        debug=True,
        database_url=database_url,
        secret_key="test-" + "x" * 64,
        admin_password="admin-pass",
        user_password="user-pass",
        **mongo_settings,
    )
    with TestClient(create_app(settings)) as test_client:
        with Session(test_client.app.state.engine) as db:
            db.add_all([
                Product(name=f"Product {index}", category="electronics",
                        price=index * 10, is_available=index % 2 == 1)
                for index in range(1, 6)
            ])
            db.commit()
        database = test_client.app.state.mongo_database
        try:
            yield test_client
        finally:
            test_client.portal.call(database.client.drop_database, database.name)


@pytest.fixture
def admin_headers(client):
    response = client.post(
        "/auth/obtain_token",
        data={"username": "admin", "password": "admin-pass"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
