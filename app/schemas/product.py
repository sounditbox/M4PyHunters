from __future__ import annotations

from typing import Annotated, Self

from pydantic import BaseModel, Field, ConfigDict, field_validator, \
    model_validator

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


class ProductSpecs(BaseModel):
    weight_grams: int = Field(gt=0)
    color: str | None = Field(default=None, max_length=30)
    tags: list[Tag] = Field(default_factory=list, max_length=10)


class ProductBase(BaseModel):
    name: ProductName
    category: CategoryName
    price: PositivePrice
    description: str | None = Field(default=None, max_length=500)
    is_available: bool = True
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


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=80)
    category: str | None = Field(default=None, min_length=2, max_length=40)
    price: float | None = Field(default=None, gt=0)
    description: str | None = None
    is_available: bool | None = None