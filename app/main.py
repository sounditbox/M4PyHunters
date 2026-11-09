from __future__ import annotations

import logging
from math import isfinite

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pymongo.errors import ConnectionFailure
from sqlalchemy import func
from sqlmodel import select
from starlette import status
from starlette.responses import JSONResponse

from app.core.config import get_settings, Settings
from app.core.lifespan import lifespan
from app.dependencies.db import SessionDep
from app.models.products import Product
from app.routers import product, product_attributes, auth, user
from app.services.product import ProductNotFoundError, InvalidProductDataError
from app.services.product_attributes import (
    ProductAttributesConflictError, ProductAttributesNotFoundError,
)

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
    application.include_router(product_attributes.router)
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

    @application.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        # Non-finite input must not break JSON serialization of validation errors.
        errors = jsonable_encoder(
            exc.errors(),
            custom_encoder={float: lambda value: value if isfinite(value) else str(value)},
        )
        return JSONResponse(status_code=422, content={"detail": errors})

    @application.exception_handler(ProductAttributesNotFoundError)
    async def attributes_not_found(request, exc):
        return JSONResponse(
            status_code=404, content={"detail": "Характеристики товара не найдены"},
        )

    @application.exception_handler(ProductAttributesConflictError)
    async def attributes_conflict(request, exc):
        return JSONResponse(
            status_code=409, content={"detail": "Повторите изменение характеристик"},
        )

    @application.exception_handler(ConnectionFailure)
    async def mongo_unavailable(request, exc):
        return JSONResponse(
            status_code=503, content={"detail": "MongoDB временно недоступна"},
        )

    return application


app = create_app()
