from __future__ import annotations

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=3, max_length=80)
    category: str = Field(min_length=2, max_length=40)
    price: float = Field(gt=0)
    description: str | None = None
    is_available: bool = True


class ProductRead(BaseModel):
    id: int = Field(ge=1)
    category: str
    name: str
    price: float
    description: str | None = None
    is_available: bool


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=80)
    category: str | None = Field(default=None, min_length=2, max_length=40)
    price: float | None = Field(default=None, gt=0)
    description: str | None = None
    is_available: bool | None = None
