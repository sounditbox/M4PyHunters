from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt,
    StrictStr, field_validator,
)

from app.schemas.product import ProductRead

AttributeKey = Annotated[
    str, Field(pattern=r"^[a-z][a-z0-9_]{0,39}$"),
]
AttributeValue = StrictStr | StrictInt | StrictFloat | StrictBool


class ProductAttributesPut(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    attributes: dict[AttributeKey, AttributeValue] = Field(
        min_length=1, max_length=50,
    )

    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, value):
        if {"weight_grams", "color", "tags"} & value.keys():
            raise ValueError("Общие характеристики изменяются через Product.specs")
        for item in value.values():
            if isinstance(item, str) and len(item) > 200:
                raise ValueError("Значение характеристики длиннее 200 символов")
            if type(item) is int and not -(2**63) <= item < 2**63:
                raise ValueError("Целое число не помещается в BSON int64")
        return value


class ProductAttributesPatch(ProductAttributesPut):
    pass


class ProductAttributesRead(BaseModel):
    id: str
    product_id: int
    attributes: dict[AttributeKey, AttributeValue]
    created_at: datetime
    updated_at: datetime


class ProductWithAttributesRead(ProductRead):
    attributes: dict[AttributeKey, AttributeValue] | None = None
