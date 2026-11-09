from datetime import UTC, datetime
from typing import Any, Mapping

from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.schemas.product import ProductRead
from app.schemas.product_attributes import (
    ProductAttributesPatch, ProductAttributesPut, ProductAttributesRead,
    ProductWithAttributesRead,
)


class ProductAttributesNotFoundError(Exception):
    pass


class ProductAttributesConflictError(Exception):
    pass


def attributes_to_read(document: Mapping[str, Any]) -> ProductAttributesRead:
    payload = dict(document)
    payload["id"] = str(payload.pop("_id"))
    return ProductAttributesRead.model_validate(payload)


async def put_attributes(
    product_id: int, payload: ProductAttributesPut, database: AsyncDatabase,
) -> ProductAttributesRead:
    now = datetime.now(UTC)
    collection = database["product_attributes"]
    query = {"product_id": product_id}
    changes = {
        "$set": {"attributes": payload.attributes, "updated_at": now},
        "$setOnInsert": {"created_at": now},
    }
    try:
        document = await collection.find_one_and_update(
            query, changes, upsert=True, return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        # Другой запрос успел первым создать документ с тем же product_id.
        document = await collection.find_one_and_update(
            query, changes, upsert=False, return_document=ReturnDocument.AFTER,
        )
    if document is None:
        # Между конфликтом вставки и повтором документ могли удалить.
        raise ProductAttributesConflictError
    return attributes_to_read(document)


async def add_attributes(
    products: list[ProductRead], database: AsyncDatabase,
) -> list[ProductWithAttributesRead]:
    if not products:
        return []
    cursor = database["product_attributes"].find(
        {"product_id": {"$in": [product.id for product in products]}},
        {"_id": 0, "product_id": 1, "attributes": 1},
    )
    by_id = {
        document["product_id"]: document["attributes"]
        async for document in cursor
    }
    return [
        ProductWithAttributesRead(
            **product.model_dump(), attributes=by_id.get(product.id),
        )
        for product in products
    ]


async def patch_attributes(
    product_id: int, payload: ProductAttributesPatch, database: AsyncDatabase,
) -> ProductAttributesRead:
    changes = {
        f"attributes.{key}": value
        for key, value in payload.attributes.items()
    }
    changes["updated_at"] = datetime.now(UTC)
    document = await database["product_attributes"].find_one_and_update(
        {"product_id": product_id}, {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        raise ProductAttributesNotFoundError
    return attributes_to_read(document)


async def delete_attributes(product_id: int, database: AsyncDatabase) -> None:
    result = await database["product_attributes"].delete_one(
        {"product_id": product_id},
    )
    if result.deleted_count == 0:
        raise ProductAttributesNotFoundError
