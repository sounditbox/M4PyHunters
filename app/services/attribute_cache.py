from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict, ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings
from app.schemas.product_attributes import AttributeKey, AttributeValue

logger = logging.getLogger(__name__)


class CachedAttributes(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    attributes: dict[AttributeKey, AttributeValue]


def attribute_cache_key(product_id: int) -> str:
    return f"products:attributes:{product_id}"


async def read_cached_attributes(
        redis: Redis | None, product_ids: list[int],
) -> dict[int, dict]:
    if redis is None or not product_ids:
        return {}
    keys = [attribute_cache_key(product_id) for product_id in product_ids]
    try:
        values = await redis.mget(keys)
    except RedisError:
        logger.warning("Redis read failed; using MongoDB")
        return {}

    found = {}
    for product_id, raw in zip(product_ids, values):
        if raw is not None:
            try:
                found[product_id] = CachedAttributes.model_validate_json(
                    raw).attributes
            except ValidationError:
                logger.warning("Invalid cache for product %s", product_id)
    return found


async def write_cached_attributes(
        redis: Redis | None, by_id: dict[int, dict], ttl: int,
) -> None:
    if redis is None or not by_id:
        return
    try:
        async with redis.pipeline(transaction=False) as pipe:
            for product_id, attributes in by_id.items():
                value = CachedAttributes(
                    attributes=attributes).model_dump_json()
                await pipe.set(
                    attribute_cache_key(product_id), value,
                    ex=ttl,
                )
            await pipe.execute()
    except RedisError:
        logger.warning("Redis fill failed; returning source data")


async def invalidate_cached_attributes(
        redis: Redis | None, product_id: int,
) -> None:
    if redis is None:
        return
    try:
        await redis.delete(attribute_cache_key(product_id))
    except RedisError:
        logger.warning(
            "Redis invalidation failed for product %s; relying on TTL",
            product_id)
