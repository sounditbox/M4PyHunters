from fastapi import APIRouter

from app.dependencies._redis import RedisDep
from app.dependencies.auth import AdminUserDep
from app.dependencies.mongodb import MongoDatabaseDep
from app.dependencies.product import ExistingProductIdDep
from app.schemas.product_attributes import (
    ProductAttributesPatch, ProductAttributesPut, ProductAttributesRead,
)
from app.services.attribute_cache import invalidate_cached_attributes
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
    redis: RedisDep,
) -> ProductAttributesRead:
    response = await put_attributes(product_id, payload, database)
    await invalidate_cached_attributes(redis, product_id)
    return response


@router.patch("/{product_id}/attributes", response_model=ProductAttributesRead)
async def update_product_attributes(
    payload: ProductAttributesPatch,
    _admin: AdminUserDep,
    product_id: ExistingProductIdDep,
    database: MongoDatabaseDep,
    redis: RedisDep,
) -> ProductAttributesRead:
    response = await patch_attributes(product_id, payload, database)
    await invalidate_cached_attributes(redis, product_id)
    return response


@router.delete("/{product_id}/attributes", status_code=204)
async def remove_product_attributes(
    _admin: AdminUserDep,
    product_id: ExistingProductIdDep,
    database: MongoDatabaseDep,
    redis: RedisDep,
) -> None:
    await delete_attributes(product_id, database)
    await invalidate_cached_attributes(redis, product_id)
