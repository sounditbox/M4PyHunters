import pytest


def test_list_products(client, admin_headers):
    response = client.get("/products", headers=admin_headers)

    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == [1, 3, 5]

    response = client.get(
        "/products",
        params={"only_available": False},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_create_product(client, admin_headers):
    response = client.post(
        "/products",
        json={"name": "Gaming Mouse", "category": "electronics", "price": 49.9},
        headers=admin_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 6
    assert body["name"] == "Gaming Mouse"
    assert body["price"] == 49.9

    saved = client.get(f"/products/{body['id']}", headers=admin_headers)
    assert saved.status_code == 200
    assert saved.json() == body


def test_update_product(client, admin_headers):
    response = client.patch(
        "/products/1",
        json={"price": 99.9},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["price"] == 99.9
    assert response.json()["name"] == "Product 1"

    saved = client.get("/products/1", headers=admin_headers)
    assert saved.status_code == 200
    assert saved.json()["price"] == 99.9


def test_replace_product(client, admin_headers):
    replacement = {"name": "Product 42", "category": "electronics",
                   "price": 1234,
                   "description": "Product 1 super description",
                   "is_available": False, "specs": None, "sale_price": None,
                   "stock_count": 0}

    response = client.put(
        '/products/1',
        json=replacement,
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == replacement | {"id": 1}

    saved = client.get("/products/1", headers=admin_headers)
    assert saved.status_code == 200
    assert saved.json() == replacement | {"id": 1}


def test_delete_product(client, admin_headers):
    response = client.delete("/products/1", headers=admin_headers)

    assert response.status_code == 204
    assert response.content == b""

    response = client.get("/products/1", headers=admin_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


@pytest.mark.parametrize("price", [0, -1])
def test_invalid_price(client, admin_headers, price):
    response = client.post(
        "/products",
        json={"name": "Gaming Mouse", "category": "electronics",
              "price": price},
        headers=admin_headers,
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"] == ["body", "price"] for error in errors)


def test_stock_count_is_saved(client, admin_headers):
    payload = {
        "name": "Gaming Mouse", "category": "electronics", "price": 49.9,
        "stock_count": 12,
        "specs": {"weight_grams": 80, "color": "black", "tags": ["gaming"]},
    }
    created = client.post("/products", json=payload, headers=admin_headers)
    assert created.status_code == 201
    product_id = created.json()["id"]
    assert created.json()["stock_count"] == 12
    assert created.json()["specs"] == payload["specs"]

    patched = client.patch(
        f"/products/{product_id}", json={"stock_count": 0}, headers=admin_headers,
    )
    assert patched.status_code == 200
    saved = client.get(f"/products/{product_id}", headers=admin_headers)
    assert saved.json()["stock_count"] == 0
    assert saved.json()["specs"] == payload["specs"]


@pytest.mark.parametrize("stock_count", [-1, None])
def test_invalid_stock_count(client, admin_headers, stock_count):
    response = client.post(
        "/products",
        json={"name": "Gaming Mouse", "category": "electronics", "price": 49.9,
              "stock_count": stock_count},
        headers=admin_headers,
    )
    assert response.status_code == 422
    response = client.patch(
        "/products/1", json={"stock_count": stock_count}, headers=admin_headers,
    )
    assert response.status_code == 422
    saved = client.get("/products/1", headers=admin_headers)
    assert saved.json()["stock_count"] == 0
