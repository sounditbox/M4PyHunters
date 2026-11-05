import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session

from app.core.logging_conf import configure_logging
from app.db.bootstrap import seed_users
from app.db.database import create_database_engine

logger = logging.getLogger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    configure_logging()
    logger.info("App starting up...")
    engine = create_database_engine(settings.database_url)
    try:
        app.state.engine = engine
        if settings.debug:
            with Session(engine) as db:
                seed_users(db, settings)
        yield
    finally:
        engine.dispose()
    logger.info("App shutting down...")
