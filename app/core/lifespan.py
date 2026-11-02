import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel, Session

from app.core.logging_conf import configure_logging
from app.db.bootstrap import seed_users
from app.db.database import create_database_engine
from app.models.products import Product  # type: ignore
from app.models.user import User # type: ignore
logger = logging.getLogger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    configure_logging()
    logger.info("App starting up...")
    engine = create_database_engine(settings.database_url)
    logger.info("Database engine created")
    try:
        SQLModel.metadata.create_all(engine)
        if settings.debug:
            with Session(engine) as db:
                seed_users(db, settings)

        logger.info("Database tables created")
        app.state.engine = engine

        yield

    finally:
        engine.dispose()
    logger.info("App shutting down...")
