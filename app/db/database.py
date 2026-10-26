from sqlalchemy import Engine
from sqlmodel import create_engine


def create_database_engine(database_url: str) -> Engine:
    options = {}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **options)
