from fastapi import APIRouter

from app.dependencies.auth import AdminUserDep
from app.dependencies.mongodb import MongoDatabaseDep
from app.dependencies.product import ExistingProductIdDep
from app.schemas.product_attributes import (
    ProductAttributesPatch, ProductAttributesPut, ProductAttributesRead,
)
from app.services.product_attributes import (
    delete_attributes, patch_attributes, put_attributes,
)

router = APIRouter(prefix="/products", tags=["Product attributes"])


@router.put("/{product_id}/attributes", response_model=ProductAttributesRead)
async def replace_product_attributes(
    payload: ProductAttributesPut,
    _admin: AdminUserDep,
    product_id: ExistingProductIdDep,
    database: MongoDatabaseDep,
) -> ProductAttributesRead:
    return await put_attributes(product_id, payload, database)


@router.patch("/{product_id}/attributes", response_model=ProductAttributesRead)
async def update_product_attributes(
    payload: ProductAttributesPatch,
    _admin: AdminUserDep,
    product_id: ExistingProductIdDep,
    database: MongoDatabaseDep,
) -> ProductAttributesRead:
    return await patch_attributes(product_id, payload, database)


@router.delete("/{product_id}/attributes", status_code=204)
async def remove_product_attributes(
    _admin: AdminUserDep,
    product_id: ExistingProductIdDep,
    database: MongoDatabaseDep,
) -> None:
    await delete_attributes(product_id, database)
