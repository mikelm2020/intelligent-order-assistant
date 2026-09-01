import pytest


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
