from typing import Annotated

from fastapi import Depends, HTTPException
from pymongo.asynchronous.database import AsyncDatabase
from starlette.requests import Request


def get_mongo_database(request: Request) -> AsyncDatabase:
    database = request.app.state.mongo_database
    if database is None:
        raise HTTPException(status_code=503, detail="MongoDB не настроена")
    return database


MongoDatabaseDep = Annotated[AsyncDatabase, Depends(get_mongo_database)]
