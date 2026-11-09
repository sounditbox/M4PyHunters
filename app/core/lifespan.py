import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import AsyncMongoClient
from sqlmodel import Session

from app.core.logging_conf import configure_logging
from app.db.bootstrap import seed_users
from app.db.database import create_database_engine
from app.db.mongodb import ensure_product_attribute_indexes

logger = logging.getLogger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    configure_logging()
    logger.info("App starting up...")
    engine = create_database_engine(settings.database_url)
    mongo_client = None
    app.state.engine = engine
    app.state.mongo_database = None
    try:
        if settings.debug:
            with Session(engine) as db:
                seed_users(db, settings)

        if settings.mongodb_url is not None:
            mongo_client = AsyncMongoClient(
                settings.mongodb_url, tz_aware=True,
                serverSelectionTimeoutMS=3000,
            )
            await mongo_client.admin.command("ping")
            database = mongo_client[settings.mongodb_database]
            await ensure_product_attribute_indexes(database)
            app.state.mongo_database = database
        yield
    finally:
        try:
            if mongo_client is not None:
                await mongo_client.close()
        finally:
            engine.dispose()
    logger.info("App shutting down...")
