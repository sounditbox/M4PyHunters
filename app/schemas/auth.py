from typing import Literal
from pydantic import BaseModel


class UserRead(BaseModel):
    id: int
    username: str
    role: Literal["user", "admin"] = "user"
    disabled: bool = False


class UserInDB(UserRead):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
