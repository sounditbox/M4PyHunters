from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlmodel import select
from starlette import status
from starlette.responses import JSONResponse

from app.core.config import get_settings, Settings
from app.core.lifespan import lifespan
from app.dependencies.db import SessionDep
from app.models.products import Product
from app.routers import product, auth, user
from app.services.product import ProductNotFoundError, InvalidProductDataError

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = get_settings() if settings is None else settings
    application = FastAPI(
        title=settings.app_name,
        description="Учебное API",
        version="0.2.1",
        lifespan=lifespan,
        debug=settings.debug
    )
    application.state.settings = settings
    application.include_router(product.router)
    application.include_router(auth.router)
    application.include_router(user.router)

    @application.get("/health")
    def health(db: SessionDep):
        count = db.exec(select(func.count()).select_from(Product)).one()
        return {"status": "ok", "products_count": count}

    @application.exception_handler(ProductNotFoundError)
    async def product_not_found(request, exc):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={"detail": "Product not found"})

    @application.exception_handler(InvalidProductDataError)
    async def invalid_product_data(request, exc):
        errors = [dict(e, loc=["body", *e["loc"]]) for e in exc.errors]
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(errors)},
        )
    return application


app = create_app()
