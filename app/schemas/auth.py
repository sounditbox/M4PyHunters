from typing import Literal

from pydantic import SecretStr, Field
from sqlmodel import SQLModel



class UserRead(SQLModel):
    id: int
    username: str
    role: Literal["user", "admin"] = "user"
    disabled: bool = False


class UserInDB(UserRead):
    hashed_password: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(SQLModel):
    username: str = Field(min_length=3, max_length=50,
                          pattern=r"^[A-Za-z0-9_-]+$")
    password: SecretStr = Field(min_length=8)
