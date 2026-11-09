import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from pymongo.errors import AutoReconnect, DuplicateKeyError
from sqlmodel import Session, select

from app.dependencies.mongodb import get_mongo_database
from app.models.user import User
from app.schemas.product_attributes import ProductAttributesPut
from app.services.product_attributes import put_attributes


def test_attributes_crud_and_composite_reads(client, admin_headers):
    path = "/products/1/attributes"
    original = client.get("/products/1", headers=admin_headers).json()
    assert original["attributes"] is None
    attributes = {"layout": "ANSI", "switch": "brown", "wireless": False}
    created = client.put(path, json={"attributes": attributes}, headers=admin_headers)
    assert created.status_code == 200
    document = created.json()
    assert ObjectId.is_valid(document["id"])
    assert document["product_id"] == 1
    assert document["attributes"] == attributes
    assert datetime.fromisoformat(document["created_at"]).tzinfo is not None

    patched = client.patch(
        path, json={"attributes": {"wireless": True}}, headers=admin_headers,
    )
    assert patched.status_code == 200
    assert patched.json()["attributes"] == attributes | {"wireless": True}
    assert patched.json()["id"] == document["id"]
    assert patched.json()["created_at"] == document["created_at"]
    assert patched.json()["updated_at"] >= document["updated_at"]
    saved = client.get("/products/1", headers=admin_headers)
    assert saved.json() == original | {"attributes": patched.json()["attributes"]}
    products = client.get("/products", headers=admin_headers).json()
    assert products[0] == saved.json()
    assert products[1]["attributes"] is None

    replaced = client.put(
        path, json={"attributes": {"layout": "ISO"}}, headers=admin_headers,
    )
    assert replaced.status_code == 200
    assert replaced.json()["attributes"] == {"layout": "ISO"}
    assert replaced.json()["id"] == document["id"]
    assert replaced.json()["created_at"] == document["created_at"]
    assert client.get("/products/1", headers=admin_headers).json() == (
        original | {"attributes": {"layout": "ISO"}}
    )

    removed = client.delete(path, headers=admin_headers)
    assert removed.status_code == 204
    assert removed.content == b""
    assert client.get("/products/1", headers=admin_headers).json() == original
    assert client.delete(path, headers=admin_headers).status_code == 404
    assert client.patch(
        path, json={"attributes": attributes}, headers=admin_headers,
    ).status_code == 404


@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_attributes_require_admin_and_existing_product(client, admin_headers, method):
    payload = {} if method == "delete" else {"json": {"attributes": {"panel": "IPS"}}}
    request = getattr(client, method)
    path = "/products/1/attributes"
    assert request(path, **payload).status_code == 401
    login = client.post(
        "/auth/obtain_token", data={"username": "user", "password": "user-pass"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert request(path, headers=headers, **payload).status_code == 403
    assert request(
        "/products/999999/attributes", headers=admin_headers, **payload,
    ).json() == {"detail": "Product not found"}
    assert request(
        "/products/0/attributes", headers=admin_headers, **payload,
    ).status_code == 422


@pytest.mark.parametrize("attributes", [
    {}, {"$set": 1}, {"panel.type": "IPS"}, {"Uppercase": "value"},
    {"a" * 41: 1}, {"nested": {"key": 1}}, {"array": [1]}, {"null": None},
    {"color": "black"}, {"weight_grams": 80}, {"tags": "gaming"},
    {"text": "x" * 201}, {"big": 2**63}, {"small": -(2**63) - 1},
    {f"key_{index}": index for index in range(51)},
])
def test_invalid_attributes_are_rejected(client, admin_headers, attributes):
    for method in [client.put, client.patch]:
        response = method(
            "/products/1/attributes", json={"attributes": attributes},
            headers=admin_headers,
        )
        assert response.status_code == 422
    assert client.get("/products/1", headers=admin_headers).json()["attributes"] is None


def test_attributes_keep_scalar_types_and_reject_extra_fields(client, admin_headers):
    path = "/products/1/attributes"
    attributes = {"text": "123", "integer": 42, "decimal": 1.5, "boolean": False,
                  "min_int": -(2**63), "max_int": 2**63 - 1}
    result = client.put(path, json={"attributes": attributes}, headers=admin_headers)
    assert result.status_code == 200
    for key, value in result.json()["attributes"].items():
        assert value == attributes[key]
        assert type(value) is type(attributes[key])
    for payload in [{}, {"attributes": {"panel": "IPS"}, "product_id": 2}]:
        assert client.put(path, json=payload, headers=admin_headers).status_code == 422
    for number in ["NaN", "Infinity", "-Infinity", "1e400"]:
        response = client.put(
            path, content='{"attributes":{"number":' + number + '}}',
            headers=admin_headers | {"Content-Type": "application/json"},
        )
        assert response.status_code == 422


def test_user_can_read_attributes_but_blocked_user_cannot(client, admin_headers):
    client.put(
        "/products/1/attributes", json={"attributes": {"panel": "IPS"}},
        headers=admin_headers,
    )
    login = client.post(
        "/auth/obtain_token", data={"username": "user", "password": "user-pass"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/products/1", headers=headers).json()["attributes"] == {"panel": "IPS"}
    assert client.get("/products", headers=headers).status_code == 200

    with Session(client.app.state.engine) as db:
        user = db.exec(select(User).where(User.username == "user")).one()
        user.disabled = True
        db.add(user)
        db.commit()
    assert client.get("/products/1", headers=headers).status_code == 403


def test_disabled_mongo_preserves_auth_sql_and_health(client, admin_headers):
    client.app.state.mongo_database = None
    assert client.get("/products").status_code == 401
    assert client.get("/products/1").status_code == 401
    assert client.get("/products/999999", headers=admin_headers).status_code == 404
    for path in ["/products/1", "/products"]:
        assert client.get(path, headers=admin_headers).status_code == 503
    assert client.get("/health").status_code == 200
    created = client.post(
        "/products", json={"name": "Gaming Mouse", "category": "electronics", "price": 49.9},
        headers=admin_headers,
    )
    assert created.status_code == 201
    assert "attributes" not in created.json()
    assert client.patch(
        "/products/1", json={"price": 22}, headers=admin_headers,
    ).status_code == 200


@pytest.mark.parametrize("method,path", [
    ("get", "/products/1"), ("get", "/products"),
    ("put", "/products/1/attributes"), ("patch", "/products/1/attributes"),
    ("delete", "/products/1/attributes"),
])
def test_mongo_connection_failure_returns_503(client, admin_headers, method, path):
    collection = MagicMock()
    collection.find.side_effect = AutoReconnect("connection lost")
    collection.find_one_and_update = AsyncMock(side_effect=AutoReconnect("connection lost"))
    collection.delete_one = AsyncMock(side_effect=AutoReconnect("connection lost"))
    client.app.dependency_overrides[get_mongo_database] = lambda: {"product_attributes": collection}
    payload = {"json": {"attributes": {"panel": "IPS"}}} if method in {"put", "patch"} else {}
    response = getattr(client, method)(path, headers=admin_headers, **payload)
    assert response.status_code == 503
    assert response.json() == {"detail": "MongoDB временно недоступна"}


def test_concurrent_first_puts_and_unique_index(client):
    database = client.app.state.mongo_database

    async def concurrent_puts():
        results = await asyncio.gather(*[
            put_attributes(1, ProductAttributesPut(attributes={"revision": index}), database)
            for index in range(10)
        ])
        assert len({result.id for result in results}) == 1
        assert await database["product_attributes"].count_documents({"product_id": 1}) == 1
        with pytest.raises(DuplicateKeyError):
            await database["product_attributes"].insert_one({"product_id": 1})

    client.portal.call(concurrent_puts)


@pytest.mark.parametrize("deleted_before_retry", [False, True])
def test_first_put_conflict_is_retried(client, admin_headers, deleted_before_retry):
    now = datetime.now(UTC)
    document = {"_id": ObjectId(), "product_id": 1, "attributes": {"panel": "IPS"},
                "created_at": now, "updated_at": now}
    collection = MagicMock()
    collection.find_one_and_update = AsyncMock(side_effect=[
        DuplicateKeyError("concurrent insert"), None if deleted_before_retry else document,
    ])
    client.app.dependency_overrides[get_mongo_database] = lambda: {"product_attributes": collection}
    response = client.put(
        "/products/1/attributes", json={"attributes": {"panel": "IPS"}},
        headers=admin_headers,
    )
    assert response.status_code == (409 if deleted_before_retry else 200)
    if not deleted_before_retry:
        assert response.json()["id"] == str(document["_id"])


def test_sql_delete_does_not_cascade_to_mongo(client, admin_headers):
    client.put(
        "/products/1/attributes", json={"attributes": {"panel": "IPS"}},
        headers=admin_headers,
    )
    assert client.delete("/products/1", headers=admin_headers).status_code == 204
    assert client.get("/products/1", headers=admin_headers).status_code == 404
    collection = client.app.state.mongo_database["product_attributes"]
    assert client.portal.call(collection.count_documents, {"product_id": 1}) == 1
