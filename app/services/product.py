from __future__ import annotations

from app.schemas.product import ProductRead, ProductCreate, ProductUpdate


class ServiceError(Exception):
    pass


class ProductNotFoundError(ServiceError):
    pass


# Сервисный слой
# работа с продуктами в бд
class ProductService:
    @staticmethod
    def get_product_by_id(product_id: int, db: dict) -> ProductRead | None:
        if product_id not in db:
            raise ProductNotFoundError
        return db[product_id]

    @staticmethod
    def get_products(
            search: str,
            limit: int,
            category: str,
            only_available: bool,
            db: dict
    ) -> list[ProductRead]:
        products = list(db.values())
        if only_available:
            products = [p for p in products if p["is_available"]]
        if category:
            products = [p for p in products if p["category"] == category]
        if search:
            products = [product for product in products if
                        search.lower() in product["name"].lower()]
        return products[:limit]

    @staticmethod
    def create(product: ProductCreate, db: dict) -> ProductRead:
        next_id = max(db.keys()) + 1
        product_dict: dict = product.model_dump()
        product_dict["id"] = next_id
        db[next_id] = product_dict
        return product_dict

    @staticmethod
    def replace(product_id: int, to_replace: ProductCreate, db: dict) -> ProductRead:
        product = ProductService.get_product_by_id(product_id, db)
        product.update(to_replace.model_dump())
        return product

    @staticmethod
    def update(product_id: int, to_update: ProductUpdate, db: dict) -> ProductRead:
        product: dict = ProductService.get_product_by_id(product_id, db)
        to_validate = product | to_update.model_dump(exclude_unset=True)
        db[product_id] = ProductRead.model_validate(to_validate).model_dump()
        return db[product_id]

    @staticmethod
    def delete(product_id: int, db: dict) -> ProductRead:
        if product_id not in db:
            raise ProductNotFoundError
        db.pop(product_id)
