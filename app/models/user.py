
from typing import TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.products import Product


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int = Field(primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50)
    hashed_password: str
    role: str = "user"
    disabled: bool = False
    products: list['Product'] = Relationship(back_populates="created_by")
