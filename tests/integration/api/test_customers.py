import pytest
from httpx2 import AsyncClient


@pytest.mark.asyncio
async def test_create_customer(client):
    response = await client.post(
        "/api/v1/customers",
        json={
            "name": "Miguel Lopez",
            "email": "miguel@example.com",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Miguel Lopez"
    assert data["email"] == "miguel@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_customer_with_duplicate_email_returns_409(client):
    payload = {
        "name": "Miguel Lopez",
        "email": "miguel@example.com",
    }

    first_response = await client.post(
        "/api/v1/customers",
        json=payload,
    )

    second_response = await client.post(
        "/api/v1/customers",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Customer email already exists"


@pytest.mark.asyncio
async def test_list_customers(client):
    await client.post(
        "/api/v1/customers",
        json={
            "name": "Miguel Lopez",
            "email": "miguel@example.com",
        },
    )

    response = await client.get("/api/v1/customers")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["email"] == "miguel@example.com"


@pytest.mark.asyncio
async def test_get_customer(client):
    create_response = await client.post(
        "/api/v1/customers",
        json={
            "name": "Miguel Lopez",
            "email": "miguel@example.com",
        },
    )

    customer_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/customers/{customer_id}")

    assert response.status_code == 200
    assert response.json()["id"] == customer_id


@pytest.mark.asyncio
async def test_get_nonexistent_customer_returns_404(client):
    response = await client.get("/api/v1/customers/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


async def test_update_customer_name(client: AsyncClient) -> None:
    create_response = await client.post(
        "/api/v1/customers",
        json={
            "name": "Miguel Lopez",
            "email": "miguel@example.com",
        },
    )

    customer_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/customers/{customer_id}",
        json={
            "name": "Miguel Angel Lopez",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Miguel Angel Lopez"
    assert response.json()["email"] == "miguel@example.com"


async def test_update_customer_email(client: AsyncClient) -> None:
    create_response = await client.post(
        "/api/v1/customers",
        json={
            "name": "Miguel Lopez",
            "email": "miguel@example.com",
        },
    )

    customer_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/customers/{customer_id}",
        json={
            "email": "miguel.new@example.com",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "miguel.new@example.com"


async def test_update_nonexistent_customer_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.patch(
        "/api/v1/customers/9999",
        json={
            "name": "Updated Name",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


async def test_update_customer_with_duplicate_email_returns_409(
    client: AsyncClient,
) -> None:
    first_response = await client.post(
        "/api/v1/customers",
        json={
            "name": "Customer One",
            "email": "one@example.com",
        },
    )

    await client.post(
        "/api/v1/customers",
        json={
            "name": "Customer Two",
            "email": "two@example.com",
        },
    )

    customer_id = first_response.json()["id"]

    response = await client.patch(
        f"/api/v1/customers/{customer_id}",
        json={
            "email": "two@example.com",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Customer email already exists"


async def test_delete_customer(client: AsyncClient) -> None:
    create_response = await client.post(
        "/api/v1/customers",
        json={
            "name": "Customer To Delete",
            "email": "delete@example.com",
        },
    )

    customer_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/customers/{customer_id}")

    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/customers/{customer_id}")

    assert get_response.status_code == 404


async def test_delete_nonexistent_customer_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.delete("/api/v1/customers/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


async def test_delete_customer_with_orders_returns_409(
    client: AsyncClient,
) -> None:
    customer_response = await client.post(
        "/api/v1/customers",
        json={
            "name": "Customer With Order",
            "email": "orders@example.com",
        },
    )

    product_response = await client.post(
        "/api/v1/products",
        json={
            "sku": "PROD-DELETE-001",
            "name": "Test Product",
            "description": None,
            "price": "100.00",
            "stock": 10,
            "active": True,
        },
    )

    customer_id = customer_response.json()["id"]
    product_id = product_response.json()["id"]

    order_response = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                }
            ],
        },
    )

    assert order_response.status_code == 201

    response = await client.delete(f"/api/v1/customers/{customer_id}")

    assert response.status_code == 409
    assert response.json()["detail"] == "Customer with orders cannot be deleted"

    get_response = await client.get(f"/api/v1/customers/{customer_id}")

    assert get_response.status_code == 200
