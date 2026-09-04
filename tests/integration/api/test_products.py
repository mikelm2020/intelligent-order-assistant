import pytest
from httpx2 import AsyncClient


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


async def test_update_product_name(client: AsyncClient) -> None:
    create_response = await client.post(
        "/api/v1/products",
        json={
            "sku": "PROD-001",
            "name": "Original Product",
            "description": "Original description",
            "price": "100.00",
            "stock": 10,
            "active": True,
        },
    )

    product_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/products/{product_id}",
        json={
            "name": "Updated Product",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Product"
    assert response.json()["sku"] == "PROD-001"
    assert response.json()["stock"] == 10


async def test_update_product_sku(client: AsyncClient) -> None:
    create_response = await client.post(
        "/api/v1/products",
        json={
            "sku": "PROD-001",
            "name": "Test Product",
            "description": None,
            "price": "100.00",
            "stock": 10,
            "active": True,
        },
    )

    product_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/products/{product_id}",
        json={
            "sku": "PROD-002",
        },
    )

    assert response.status_code == 200
    assert response.json()["sku"] == "PROD-002"


async def test_update_product_price_stock_and_active(
    client: AsyncClient,
) -> None:
    create_response = await client.post(
        "/api/v1/products",
        json={
            "sku": "PROD-001",
            "name": "Test Product",
            "description": None,
            "price": "100.00",
            "stock": 10,
            "active": True,
        },
    )

    product_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/products/{product_id}",
        json={
            "price": "150.00",
            "stock": 25,
            "active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["price"] == "150.00"
    assert response.json()["stock"] == 25
    assert response.json()["active"] is False


async def test_update_nonexistent_product_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.patch(
        "/api/v1/products/9999",
        json={
            "name": "Updated Product",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


async def test_update_product_with_duplicate_sku_returns_409(
    client: AsyncClient,
) -> None:
    first_response = await client.post(
        "/api/v1/products",
        json={
            "sku": "PROD-001",
            "name": "Product One",
            "description": None,
            "price": "100.00",
            "stock": 10,
            "active": True,
        },
    )

    await client.post(
        "/api/v1/products",
        json={
            "sku": "PROD-002",
            "name": "Product Two",
            "description": None,
            "price": "200.00",
            "stock": 20,
            "active": True,
        },
    )

    product_id = first_response.json()["id"]

    response = await client.patch(
        f"/api/v1/products/{product_id}",
        json={
            "sku": "PROD-002",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Product SKU already exists"
