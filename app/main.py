from fastapi import FastAPI
from starlette import status
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.lifespan import lifespan
from app.dependencies.db import DbDep
from app.routers import product, auth
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
    app.include_router(auth.router)

    @app.get("/health")
    def health(db: DbDep):
        return {"status": "ok", "products_count": len(db)}

    @app.exception_handler(ProductNotFoundError)
    async def product_not_found():
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={"detail": "Product not found"})
    return app


app = create_app()
