from typing import Annotated, Iterator

from fastapi import Depends
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.requests import Request

from app.db.fake_db import get_db
from app.db.fake_users import get_users
from app.schemas.auth import UserInDB

UsersDep = Annotated[dict[str, UserInDB], Depends(get_users)]
DbDep = Annotated[dict, Depends(get_db)]

def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


async def get_async_session(request: Request) -> Iterator[AsyncSession]:
    async with AsyncSession(request.app.state.engine) as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

SessionDep = Annotated[Session, Depends(get_session)]
