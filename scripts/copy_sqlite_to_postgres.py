import argparse
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.db.database import create_database_engine
from app.models import Product, User


def copy_data(source_database_url: str, target_database_url: str) -> dict[str, int]:
    """Copy the L8 catalog into an empty, migrated PostgreSQL database."""
    source_url = make_url(source_database_url)
    target_url = make_url(target_database_url)
    if source_url.get_backend_name() != "sqlite":
        raise RuntimeError("Источник должен быть SQLite")
    if not source_url.database or not Path(source_url.database).is_file():
        raise RuntimeError("Файл SQLite не найден")
    if target_url.get_backend_name() != "postgresql":
        raise RuntimeError("Назначение должно быть PostgreSQL")

    source_engine = create_database_engine(source_database_url)
    target_engine = create_database_engine(target_url.render_as_string(hide_password=False))
    counts = {}
    try:
        with source_engine.connect() as source, target_engine.begin() as target:
            for connection in (source, target):
                versions = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalars().all()
                if versions != ["0002"]:
                    raise RuntimeError("Обе базы должны быть на ревизии 0002")
            tables = (User.__table__, Product.__table__)
            for table in tables:
                if target.scalar(select(func.count()).select_from(table)):
                    raise RuntimeError("Таблицы PostgreSQL должны быть пустыми")

            for table in tables:
                rows = source.execute(select(table)).mappings().all()
                if rows:
                    target.execute(table.insert(), [dict(row) for row in rows])
                sequence = target.scalar(
                    text("SELECT pg_get_serial_sequence(:table_name, 'id')"),
                    {"table_name": table.name},
                )
                if sequence is None:
                    raise RuntimeError(f"Не найдена sequence таблицы {table.name}")
                last_id = target.scalar(select(func.max(table.c.id)))
                target.execute(
                    text("SELECT setval(CAST(:sequence AS regclass), :value, :called)"),
                    {"sequence": sequence, "value": last_id or 1,
                     "called": last_id is not None},
                )
                counts[table.name] = len(rows)
    finally:
        target_engine.dispose()
        source_engine.dispose()
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-url", required=True)
    args = parser.parse_args()
    counts = copy_data(args.source_url, get_settings().database_url)
    for table, count in counts.items():
        print(f"{table}: скопировано {count} строк")


if __name__ == "__main__":
    main()
