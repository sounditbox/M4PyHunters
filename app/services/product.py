from __future__ import annotations

from pydantic import ValidationError
from sqlmodel import select, col, Session

from app.models.products import Product
from app.schemas.product import ProductRead, ProductCreate, ProductUpdate


class ServiceError(Exception):
    pass


class ProductNotFoundError(ServiceError):
    pass


class InvalidProductDataError(ServiceError):
    def __init__(self, errors: list[dict]):
        super().__init__("Invalid product data")
        self.errors = errors


def get_product_by_id(product_id: int, db: Session) -> ProductRead | None:
    product = db.get(Product, product_id)
    if not product:
        raise ProductNotFoundError
    return product


def get_products(
        search: str, limit: int, category: str, only_available: bool,
        db: Session
) -> list[ProductRead]:
    statement = select(Product)
    if only_available:
        statement = statement.where(col(Product.is_available).is_(True))
    if category:
        statement = statement.where(Product.category == category)
    if search:
        statement = statement.where(
            col(Product.name).icontains(search, autoescape=True)
        )
    statement = statement.limit(limit)
    return db.exec(statement).all()


def create(product: ProductCreate, db: Session, created_by_id: int) -> Product:
    saved = Product(**product.model_dump() | {"created_by_id": created_by_id})
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


def replace(product_id: int, to_replace: ProductCreate,
            db: Session) -> Product:
    product = get_product_by_id(product_id, db)
    product.sqlmodel_update(to_replace.model_dump())
    db.commit()
    db.refresh(product)
    return product


def update(product_id: int, to_update: ProductUpdate,
           db: Session) -> Product:
    product = get_product_by_id(product_id, db)
    patch = to_update.model_dump(exclude_unset=True)
    try:
        validated = ProductCreate.model_validate(product, update=patch)
    except ValidationError as exc:
        raise InvalidProductDataError(
            exc.errors(include_context=False)
        ) from exc
    product.sqlmodel_update(validated.model_dump())
    db.commit()
    db.refresh(product)
    return product


def delete(product_id: int, db: Session) -> None:
    product = get_product_by_id(product_id, db)
    db.delete(product)
    db.commit()
