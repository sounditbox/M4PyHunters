import logging
import time
from time import perf_counter
from typing import Annotated

from fastapi import FastAPI
from fastapi import Path, Query, HTTPException
from starlette import status

from app.schemas import ProductRead, ProductCreate, ProductUpdate
from app.service import ProductService, ProductNotFoundError

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Products API",
    description="Учебное API",
    version="0.2.1",
)

ProductId = Annotated[int, Path(ge=1, description="ID товара")]

SearchParam = Annotated[
    str | None, Query(min_length=2, max_length=50,
                      description="Поиск по названию товара")
]
LimitParam = Annotated[
    int, Query(ge=1, le=100, description="Количество товаров на странице")]

CategoryParam = Annotated[
    str | None, Query(min_length=2, max_length=40,
                      description="Категория товара")
]


# HTTP-контракт
@app.get("/products/{product_id}", response_model=ProductRead,
         tags=["Products"], description='Получение товара по ID')
async def get_product(product_id: ProductId) -> ProductRead:
    return ProductService.get_product_by_id(product_id)


@app.get("/products", response_model=list[ProductRead],
         tags=["Products"], description='Получение списка товаров')
async def list_products(
        search: SearchParam = None,
        limit: LimitParam = 10,
        category: CategoryParam = None,
        only_available: bool = True,
) -> list[ProductRead]:
    return ProductService.get_products(search, limit, category, only_available)


@app.post("/products", response_model=ProductRead,
          status_code=status.HTTP_201_CREATED, tags=["Products"],
          description='Создание нового товара')
async def create_product(product: ProductCreate) -> ProductRead:
    return ProductService.create(product)


@app.put("/products/{product_id}", response_model=ProductRead,
         tags=["Products"], description='Замена товара')
async def replace_product(product_id: ProductId,
                    to_replace: ProductCreate) -> ProductRead:
    return ProductService.replace(product_id, to_replace)


@app.patch('/products/{product_id}', response_model=ProductRead,
           tags=["Products"], description='Обновление товара')
async def update_product(product_id: ProductId,
                   to_update: ProductUpdate) -> ProductRead:
    return ProductService.update(product_id, to_update)


@app.delete('/products/{product_id}', tags=["Products"],
            status_code=status.HTTP_204_NO_CONTENT,
            description='Удаление товара'
            )
async def delete_product(product_id: ProductId) -> None:
    ProductService.delete(product_id)


@app.exception_handler(ProductNotFoundError)
async def product_not_found():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Product not found")
