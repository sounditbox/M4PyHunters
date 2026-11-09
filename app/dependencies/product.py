from typing import Annotated

from fastapi import Depends, Path

from app.dependencies.auth import CurrentUserDep
from app.dependencies.db import SessionDep
from app.schemas.product import ProductRead
from app.services.product import get_product_by_id


def require_product(
    product_id: Annotated[int, Path(ge=1)],
    db: SessionDep,
    _user: CurrentUserDep,
) -> ProductRead:
    return ProductRead.model_validate(get_product_by_id(product_id, db))


ExistingProductDep = Annotated[ProductRead, Depends(require_product)]


def require_product_id(product: ExistingProductDep) -> int:
    return product.id


ExistingProductIdDep = Annotated[int, Depends(require_product_id)]
