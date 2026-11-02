
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field, Relationship

from app.schemas.product import CategoryName, ProductName, PositivePrice

if TYPE_CHECKING:
    from app.models.user import User


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int = Field(ge=1, primary_key=True)
    name: ProductName
    category: CategoryName
    price: PositivePrice
    description: str | None = Field(default=None, max_length=500)
    is_available: bool = True
    sale_price: PositivePrice | None = None
    specs: dict | None = Field(
        default=None, sa_column=Column(JSON(none_as_null=True), nullable=True),
    )
    created_by_id: int | None = Field(default=None, foreign_key="users.id")
    created_by: Optional["User"] = Relationship(back_populates="products")
