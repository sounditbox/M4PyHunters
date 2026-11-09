from typing import Annotated

from fastapi import Depends, Path, Query, APIRouter
from starlette import status

from app.dependencies.auth import CurrentUserDep, AdminUserDep
from app.dependencies.db import SessionDep
from app.dependencies.mongodb import MongoDatabaseDep
from app.dependencies.product import ExistingProductDep
from app.schemas.product import ProductRead, ProductCreate, ProductUpdate
from app.schemas.product_attributes import ProductWithAttributesRead
from app.services.product import (
    get_products, create,
    replace, update, delete
)
from app.services.product_attributes import add_attributes

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


@router.get("/{product_id}", response_model=ProductWithAttributesRead)
async def get_product(
    product: ExistingProductDep, database: MongoDatabaseDep,
) -> ProductWithAttributesRead:
    products = await add_attributes([product], database)
    return products[0]


def load_product_list(
    db: SessionDep,
    user: CurrentUserDep,
    search: SearchParam = None,
    limit: LimitParam = 10,
    category: CategoryParam = None,
    only_available: bool = True,
) -> list[ProductRead]:
    products = get_products(search, limit, category, only_available, db)
    return [ProductRead.model_validate(product) for product in products]


ProductListDep = Annotated[list[ProductRead], Depends(load_product_list)]


@router.get("", response_model=list[ProductWithAttributesRead])
async def list_products(
    products: ProductListDep, database: MongoDatabaseDep,
) -> list[ProductWithAttributesRead]:
    return await add_attributes(products, database)


@router.post("", response_model=ProductRead,
             status_code=status.HTTP_201_CREATED,
             description='Создание нового товара')
async def create_product(product: ProductCreate, db: SessionDep,
                         _admin: AdminUserDep) -> ProductRead:
    return create(product, db, _admin.id)


@router.put("/{product_id}", response_model=ProductRead,
            description='Замена товара')
async def replace_product(product_id: ProductId,
                          to_replace: ProductCreate, db: SessionDep,
                          _admin: AdminUserDep) -> ProductRead:
    return replace(product_id, to_replace, db)


@router.patch('/{product_id}', response_model=ProductRead,
              description='Обновление товара')
async def update_product(product_id: ProductId,
                         to_update: ProductUpdate, db: SessionDep,
                         _admin: AdminUserDep) -> ProductRead:
    return update(product_id, to_update, db)


@router.delete('/{product_id}', status_code=status.HTTP_204_NO_CONTENT,
               description='Удаление товара'
               )
async def delete_product(product_id: ProductId, db: SessionDep,
                         _admin: AdminUserDep) -> None:
    delete(product_id, db)
