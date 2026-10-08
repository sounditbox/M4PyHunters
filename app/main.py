import logging

from fastapi import FastAPI, HTTPException
from starlette import status

from app.routers import products_router
from app.service import ProductNotFoundError

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Products API",
    description="Учебное API",
    version="0.2.1",
)


@app.exception_handler(ProductNotFoundError)
async def product_not_found():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Product not found")


app.include_router(products_router)
