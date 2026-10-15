import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.fake_db import fake_db
from app.core.logging_conf import configure_logging
from app.db.fake_users import fake_users

logger = logging.getLogger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("App starting up...")
    app.state.db = fake_db
    app.state.users = fake_users

    yield

    logger.info("App shutting down...")
