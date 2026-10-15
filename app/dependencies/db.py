from typing import Annotated

from fastapi import Depends

from app.db.fake_db import get_db
from app.db.fake_users import get_users
from app.schemas.auth import UserInDB

UsersDep = Annotated[dict[str, UserInDB], Depends(get_users)]

DbDep = Annotated[dict, Depends(get_db)]
