from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from starlette.requests import Request


def get_redis(request: Request) -> Redis | None:
    return request.app.state.redis


RedisDep = Annotated[Redis | None, Depends(get_redis)]
