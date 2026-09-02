from decimal import Decimal

from httpx import AsyncClient


async def create_customer(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/customers",
        json={
            "name": "Miguel Lopez",
            "email": "miguel@example.com",
        },
    )

    assert response.status_code == 201

    return response.json()


async def create_product(
    client: AsyncClient,
    *,
    sku: str = "PROD-001",
    stock: int = 10,
    price: str = "100.00",
    active: bool = True,
) -> dict:
    response = await client.post(
        "/api/v1/products",
        json={
            "sku": sku,
            "name": "Test Product",
            "description": "Integration test product",
            "price": price,
            "stock": stock,
            "active": active,
        },
    )

    assert response.status_code == 201

    return response.json()


async def test_create_order(client: AsyncClient) -> None:
    customer = await create_customer(client)
    product = await create_product(client)

    response = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer["id"]
    assert data["status"] == "pending"
    assert Decimal(data["total"]) == Decimal("200.00")

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["product_id"] == product["id"]
    assert item["quantity"] == 2
    assert Decimal(item["unit_price"]) == Decimal("100.00")
    assert Decimal(item["subtotal"]) == Decimal("200.00")


async def test_create_order_updates_product_stock(
    client: AsyncClient,
) -> None:
    customer = await create_customer(client)

    product = await create_product(
        client,
        stock=10,
    )

    response = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 3,
                }
            ],
        },
    )

    assert response.status_code == 201

    product_response = await client.get(f"/api/v1/products/{product['id']}")

    assert product_response.status_code == 200
    assert product_response.json()["stock"] == 7


async def test_create_order_with_nonexistent_customer_returns_400(
    client: AsyncClient,
) -> None:
    product = await create_product(client)

    response = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": 9999,
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Customer not found"


async def test_create_order_with_nonexistent_product_returns_400(
    client: AsyncClient,
) -> None:
    customer = await create_customer(client)

    response = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": 9999,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Product 9999 not found"


async def test_create_order_with_insufficient_stock_returns_400(
    client: AsyncClient,
) -> None:
    customer = await create_customer(client)

    product = await create_product(
        client,
        stock=2,
    )

    response = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 3,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"] == f"Insufficient stock for product {product['id']}"
    )


async def test_create_order_with_inactive_product_returns_400(
    client: AsyncClient,
) -> None:
    customer = await create_customer(client)

    product = await create_product(
        client,
        active=False,
    )

    response = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == f"Product {product['id']} is inactive"


async def test_get_order(client: AsyncClient) -> None:
    customer = await create_customer(client)
    product = await create_product(client)

    create_response = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                }
            ],
        },
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/orders/{order_id}")

    assert response.status_code == 200
    assert response.json()["id"] == order_id


async def test_get_nonexistent_order_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/orders/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


async def test_list_orders(client: AsyncClient) -> None:
    customer = await create_customer(client)

    product = await create_product(
        client,
        stock=10,
    )

    response = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 201

    response = await client.get("/api/v1/orders")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["customer_id"] == customer["id"]


async def test_create_order_rolls_back_when_one_item_fails(
    client: AsyncClient,
) -> None:
    customer = await create_customer(client)

    product_1 = await create_product(
        client,
        sku="PROD-001",
        stock=10,
        price="100.00",
    )

    product_2 = await create_product(
        client,
        sku="PROD-002",
        stock=1,
        price="50.00",
    )

    response = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product_1["id"],
                    "quantity": 2,
                },
                {
                    "product_id": product_2["id"],
                    "quantity": 5,
                },
            ],
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"] == f"Insufficient stock for product {product_2['id']}"
    )

    product_1_response = await client.get(f"/api/v1/products/{product_1['id']}")

    product_2_response = await client.get(f"/api/v1/products/{product_2['id']}")

    assert product_1_response.status_code == 200
    assert product_2_response.status_code == 200

    assert product_1_response.json()["stock"] == 10
    assert product_2_response.json()["stock"] == 1
