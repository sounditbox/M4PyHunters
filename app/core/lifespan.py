import logging

from contextlib import asynccontextmanager
from copy import deepcopy

from fastapi import FastAPI

from app.db.fake_db import fake_db
from app.core.logging_conf import configure_logging
from app.db.fake_users import fake_users

logger = logging.getLogger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("App starting up...")
    app.state.db = deepcopy(fake_db)
    app.state.users = deepcopy(fake_users)

    yield

    logger.info("App shutting down...")
