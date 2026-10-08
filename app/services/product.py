from __future__ import annotations

from app.db import fake_db
from app.schemas.product import ProductRead, ProductCreate, ProductUpdate


class ServiceError(Exception):
    pass


class ProductNotFoundError(ServiceError):
    pass


# Сервисный слой
# работа с продуктами в бд
class ProductService:
    @staticmethod
    def get_product_by_id(product_id: int) -> ProductRead | None:
        if product_id not in fake_db:
            raise ProductNotFoundError
        return fake_db[product_id]

    @staticmethod
    def get_products(
            search: str,
            limit: int,
            category: str,
            only_available: bool
    ) -> list[ProductRead]:
        products = list(fake_db.values())
        if only_available:
            products = [p for p in products if p["available"]]
        if category:
            products = [p for p in products if p["category"] == category]
        if search:
            products = [product for product in products if
                        search.lower() in product["name"].lower()]
        return products[:limit]

    @staticmethod
    def create(product: ProductCreate) -> ProductRead:
        next_id = max(fake_db.keys()) + 1
        product_dict: dict = product.model_dump()
        product_dict["id"] = next_id
        fake_db[next_id] = product_dict
        return product_dict

    @staticmethod
    def replace(product_id: int, to_replace: ProductCreate) -> ProductRead:
        product = ProductService.get_product_by_id(product_id)
        product.update(to_replace.model_dump())
        return product

    @staticmethod
    def update(product_id: int, to_update: ProductUpdate) -> ProductRead:
        product: ProductRead = ProductService.get_product_by_id(product_id)
        to_validate = (product.model_dump(exclude=['id']) |
                       to_update.model_dump(exclude_unset=True))
        validated = ProductRead.model_validate(to_validate)
        fake_db[product_id] = validated.model_dump()
        return validated

    @staticmethod
    def delete(product_id: int) -> ProductRead:
        if product_id not in fake_db:
            raise ProductNotFoundError
        fake_db.pop(product_id)
