import pytest


@pytest.mark.asyncio
async def test_create_product(client):
    response = await client.post(
        "/api/v1/products",
        json={
            "sku": "LAPTOP-001",
            "name": "Laptop",
            "description": "Laptop para desarrollo",
            "price": "25000.00",
            "stock": 10,
            "active": True,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["sku"] == "LAPTOP-001"
    assert data["name"] == "Laptop"
    assert data["price"] == "25000.00"
    assert data["stock"] == 10
    assert data["active"] is True


@pytest.mark.asyncio
async def test_create_product_with_duplicate_sku_returns_409(client):
    payload = {
        "sku": "LAPTOP-001",
        "name": "Laptop",
        "description": "Laptop para desarrollo",
        "price": "25000.00",
        "stock": 10,
        "active": True,
    }

    first_response = await client.post(
        "/api/v1/products",
        json=payload,
    )

    second_response = await client.post(
        "/api/v1/products",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Product SKU already exists"


@pytest.mark.asyncio
async def test_list_products(client):
    await client.post(
        "/api/v1/products",
        json={
            "sku": "LAPTOP-001",
            "name": "Laptop",
            "description": "Laptop para desarrollo",
            "price": "25000.00",
            "stock": 10,
            "active": True,
        },
    )

    response = await client.get("/api/v1/products")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["sku"] == "LAPTOP-001"


@pytest.mark.asyncio
async def test_get_product(client):
    create_response = await client.post(
        "/api/v1/products",
        json={
            "sku": "LAPTOP-001",
            "name": "Laptop",
            "description": "Laptop para desarrollo",
            "price": "25000.00",
            "stock": 10,
            "active": True,
        },
    )

    product_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["id"] == product_id


@pytest.mark.asyncio
async def test_get_nonexistent_product_returns_404(client):
    response = await client.get("/api/v1/products/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"
