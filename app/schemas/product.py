from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, ConfigDict, field_validator, \
    model_validator
from sqlmodel import SQLModel

ProductName = Annotated[
    str,
    Field(min_length=3, max_length=80, examples=["Mechanical Keyboard"]),
]
CategoryName = Annotated[
    str,
    Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9-]+$", examples=["electronics"]),
]
PositivePrice = Annotated[float, Field(gt=0, le=1_000_000)]

Tag = Annotated[str, Field(min_length=2, max_length=30)]


class ProductSpecs(SQLModel):
    weight_grams: int = Field(gt=0)
    color: str | None = Field(default=None, max_length=30)
    tags: list[Tag] = Field(default_factory=list, max_length=10)


class ProductBase(SQLModel):
    name: ProductName
    category: CategoryName
    price: PositivePrice
    description: str | None = Field(default=None, max_length=500)
    is_available: bool = True
    stock_count: int = Field(default=0, ge=0)
    specs: ProductSpecs | None = None
    sale_price: PositivePrice | None = None

    @model_validator(mode="after")
    def check_sale_price(self) -> Self:
        if self.sale_price is not None and self.sale_price >= self.price:
            raise ValueError("Цена со скидкой должна быть меньше обычной цены")

        return self

    @field_validator("name")
    @classmethod
    def check_test_names(cls, value: str) -> str:
        normalized = " ".join(value.split())

        if normalized.lower() in {"test", "product", "товар"}:
            raise ValueError("Укажите содержательное название товара")

        return normalized

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return value.lower()


class ProductCreate(ProductBase):
    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ProductRead(ProductBase):
    id: int = Field(ge=1)


class ProductUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=3, max_length=80)
    category: str | None = Field(default=None, min_length=2, max_length=40)
    price: float | None = Field(default=None, gt=0)
    description: str | None = None
    is_available: bool | None = None
    stock_count: int | None = Field(default=None, ge=0)
    sale_price: float | None = None
    specs: ProductSpecs | None = None
