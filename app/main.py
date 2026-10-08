
from fastapi import FastAPI, HTTPException
from starlette import status

from app.db import DbDep
from .config import get_settings
from app.lifespan import lifespan
from app.routers import product
from app.services.product import ProductNotFoundError


def create_app():
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Учебное API",
        version="0.2.1",
        lifespan=lifespan,
        debug=settings.debug
    )
    app.include_router(product.router)

    @app.get("/health")
    def health(db: DbDep):
        return {"status": "ok", "products_count": len(db)}

    @app.exception_handler(ProductNotFoundError)
    async def product_not_found():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found")

    return app


app = create_app()
