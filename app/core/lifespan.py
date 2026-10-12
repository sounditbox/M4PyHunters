import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.fake_db import fake_db
from app.core.logging_conf import configure_logging

logger = logging.getLogger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("App starting up...")
    app.state.db = fake_db

    yield

    logger.info("App shutting down...")
