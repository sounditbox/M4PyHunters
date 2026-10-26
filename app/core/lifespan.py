import logging
from contextlib import asynccontextmanager
from copy import deepcopy

from fastapi import FastAPI
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.core.logging_conf import configure_logging
from app.db.database import create_database_engine
from app.db.fake_users import fake_users
from app.models.products import Product  # type: ignore

logger = logging.getLogger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("App starting up...")
    engine = create_database_engine(get_settings().database_url)
    logger.info("Database engine created")
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created")
        app.state.engine = engine
        app.state.users = deepcopy(fake_users)

        yield

    finally:
        engine.dispose()
    logger.info("App shutting down...")
