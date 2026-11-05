import pytest
import sqlalchemy as sa
from sqlalchemy.engine import make_url

from app.db.database import create_database_engine
from app.models import Product, User
from scripts.copy_sqlite_to_postgres import copy_data


def test_copy_preserves_data_and_advances_sequences(
    database_url, tmp_path, migrate_database,
):
    if make_url(database_url).get_backend_name() != "postgresql":
        pytest.skip("Set TEST_DATABASE_URL to test the transfer into PostgreSQL")
    target_url = database_url
    source_url = f"sqlite+pysqlite:///{tmp_path / 'source.db'}"
    migrate_database(source_url)
    migrate_database(target_url)
    source_engine = create_database_engine(source_url)
    target_engine = create_database_engine(target_url)
    try:
        with source_engine.begin() as connection:
            connection.execute(User.__table__.insert().values(
                id=7, username="copied-user", hashed_password="original-hash",
                role="admin", disabled=False,
            ))
            connection.execute(Product.__table__.insert().values(
                id=42, name="Copied Mouse", category="electronics", price=49.9,
                is_available=True, stock_count=12,
                specs={"weight_grams": 80, "color": "black", "tags": ["gaming"]},
                created_by_id=7,
            ))

        assert copy_data(source_url, target_url) == {"users": 1, "products": 1}
        with target_engine.begin() as connection:
            user = connection.execute(sa.select(User.__table__)).mappings().one()
            product = connection.execute(sa.select(Product.__table__)).mappings().one()
            assert user["id"] == 7
            assert user["hashed_password"] == "original-hash"
            assert product["id"] == 42
            assert product["created_by_id"] == 7
            assert product["stock_count"] == 12
            assert product["specs"] == {"weight_grams": 80, "color": "black", "tags": ["gaming"]}
            assert connection.execute(User.__table__.insert().values(
                username="next-user", hashed_password="next-hash", role="user",
                disabled=False,
            ).returning(User.id)).scalar_one() == 8
            assert connection.execute(Product.__table__.insert().values(
                name="Next Mouse", category="electronics", price=20,
                is_available=True, stock_count=0, created_by_id=7,
            ).returning(Product.id)).scalar_one() == 43

        with pytest.raises(RuntimeError, match="пустыми"):
            copy_data(source_url, target_url)
        with target_engine.connect() as connection:
            assert connection.scalar(sa.select(sa.func.count()).select_from(Product)) == 2
    finally:
        target_engine.dispose()
        source_engine.dispose()


def test_copy_rejects_missing_source(tmp_path):
    source = tmp_path / "missing.db"
    with pytest.raises(RuntimeError, match="не найден"):
        copy_data(f"sqlite+pysqlite:///{source}", "postgresql+psycopg://unused")
    assert not source.exists()
