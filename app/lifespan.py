import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import fake_db
from app.logging_conf import configure_logging

logger = logging.getLogger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("App starting up...")

    app.state.db = fake_db
    yield  # actual app startup
    logger.info("App shutting down...")
