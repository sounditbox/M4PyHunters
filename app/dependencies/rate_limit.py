import logging
from typing import Annotated

from fastapi import HTTPException, Depends
from redis import RedisError
from starlette.requests import Request

from app.dependencies._redis import RedisDep
from app.dependencies.settings import SettingsDep

logger = logging.getLogger(__name__)


async def limit_login_attempts(
        request: Request, redis: RedisDep, settings: SettingsDep,
) -> None:
    if redis is None:
        return
    host = request.client.host if request.client else "unknown"
    key = f"auth:login:{host}"
    try:
        async with redis.pipeline(transaction=True) as pipe:
            await pipe.incr(key)
            await pipe.expire(key, 60, nx=True)
            await pipe.ttl(key)
            attempts, _, ttl = await pipe.execute()
    except RedisError:
        logger.warning("Redis limiter unavailable; allowing password check")
        return
    if attempts > settings.auth_rate_limit_per_minute:
        raise HTTPException(
            status_code=429, detail="Слишком много попыток входа",
            headers={"Retry-After": str(max(1, ttl))},
        )


LoginRateLimitDep = Annotated[None, Depends(limit_login_attempts)]
