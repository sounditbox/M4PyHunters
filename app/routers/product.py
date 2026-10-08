from typing import Annotated

from fastapi import Path, Query, APIRouter
from starlette import status

from app.db import DbDep
from app.schemas.product import ProductRead, ProductCreate, ProductUpdate
from app.services.product import ProductService

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

router = APIRouter(prefix='/products', tags=['Products'])


@router.get("/{product_id}", response_model=ProductRead,
            description='Получение товара по ID')
async def get_product(product_id: ProductId, db: DbDep) -> ProductRead:
    return ProductService.get_product_by_id(product_id, db)


@router.get("", response_model=list[ProductRead],
            description='Получение списка товаров')
async def list_products(
        db: DbDep,
        search: SearchParam = None,
        limit: LimitParam = 10,
        category: CategoryParam = None,
        only_available: bool = True,
) -> list[ProductRead]:
    return ProductService.get_products(
        search, limit, category, only_available, db
    )


@router.post("", response_model=ProductRead,
             status_code=status.HTTP_201_CREATED,
             description='Создание нового товара')
async def create_product(product: ProductCreate, db: DbDep) -> ProductRead:
    return ProductService.create(product, db)


@router.put("/{product_id}", response_model=ProductRead,
            description='Замена товара')
async def replace_product(product_id: ProductId,
                          to_replace: ProductCreate, db: DbDep) -> ProductRead:
    return ProductService.replace(product_id, to_replace, db)


@router.patch('/{product_id}', response_model=ProductRead,
              description='Обновление товара')
async def update_product(product_id: ProductId,
                         to_update: ProductUpdate, db: DbDep) -> ProductRead:
    return ProductService.update(product_id, to_update, db)


@router.delete('/{product_id}', status_code=status.HTTP_204_NO_CONTENT,
               description='Удаление товара'
               )
async def delete_product(product_id: ProductId, db: DbDep) -> None:
    ProductService.delete(product_id, db)
