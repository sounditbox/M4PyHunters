from alembic import command
import pytest
import sqlalchemy as sa

from app.db.database import create_database_engine


def test_migrations_preserve_existing_data(database_url, migrate_database):
    config = migrate_database(database_url, "0001")
    engine = create_database_engine(database_url)
    try:
        metadata = sa.MetaData()
        users = sa.Table("users", metadata, autoload_with=engine)
        products = sa.Table("products", metadata, autoload_with=engine)
        with engine.begin() as connection:
            connection.execute(users.insert().values(
                id=7, username="migration-user", hashed_password="existing-hash",
                role="admin", disabled=False,
            ))
            connection.execute(products.insert().values(
                id=42, name="Existing Mouse", category="electronics", price=49.9,
                is_available=True, specs={"weight_grams": 80}, created_by_id=7,
            ))

        command.upgrade(config, "head")
        command.check(config)
        with engine.connect() as connection:
            row = connection.execute(sa.text(
                "SELECT name, stock_count, created_by_id FROM products WHERE id=42"
            )).one()
            assert tuple(row) == ("Existing Mouse", 0, 7)
        columns = sa.inspect(engine).get_columns("products")
        assert next(c for c in columns if c["name"] == "stock_count")["nullable"] is False
        assert sa.inspect(engine).get_foreign_keys("products")[0]["referred_table"] == "users"

        with pytest.raises(sa.exc.IntegrityError), engine.begin() as connection:
            connection.execute(sa.text("UPDATE products SET stock_count=NULL WHERE id=42"))

        command.downgrade(config, "0001")
        assert "stock_count" not in {c["name"] for c in sa.inspect(engine).get_columns("products")}
        with engine.connect() as connection:
            assert connection.scalar(sa.text("SELECT name FROM products WHERE id=42")) == "Existing Mouse"
        command.upgrade(config, "head")
        command.check(config)
        command.downgrade(config, "base")
        assert not {"users", "products"} & set(sa.inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_fresh_database_matches_models(database_url, migrate_database):
    config = migrate_database(database_url)
    command.check(config)
