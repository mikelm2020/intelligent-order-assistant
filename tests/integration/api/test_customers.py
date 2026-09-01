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
