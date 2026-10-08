import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.assistant_run import AssistantRun

OPERATOR = {"Authorization": "Bearer test-operator-key-00000000000000000"}
REVIEWER = {"Authorization": "Bearer test-reviewer-key-00000000000000000"}


async def pending_order(client):
    customer = await client.post(
        "/api/v1/customers",
        json={"name": "Demo Customer", "email": f"{uuid4()}@example.com"},
    )
    product = await client.post(
        "/api/v1/products",
        json={
            "sku": str(uuid4()),
            "name": "Demo Product",
            "price": "25.50",
            "stock": 10,
        },
    )
    order = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer.json()["id"],
            "items": [{"product_id": product.json()["id"], "quantity": 2}],
        },
    )
    assert order.status_code == 201
    return order.json()["id"], product.json()["id"]


async def request_action(client, order_id, action="cancelar"):
    response = await client.post(
        "/api/v1/assistant/ask",
        json={"question": f"Quiero {action} la orden {order_id}", "limit": 2},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "pending_approval"
    assert result["approval"]["order_id"] == order_id
    assert result["approval"]["total"] == "51.00"
    return result["run_id"]


@pytest.mark.parametrize(
    "action,expected", [("confirmar", "confirmed"), ("cancelar", "cancelled")]
)
async def test_action_requires_reviewer_and_is_replay_safe(client, action, expected):
    order_id, product_id = await pending_order(client)
    run_id = await request_action(client, order_id, action)
    assert (await client.get(f"/api/v1/orders/{order_id}")).json()[
        "status"
    ] == "pending"
    preview = await client.get(f"/api/v1/assistant/runs/{run_id}", headers=REVIEWER)
    assert preview.json()["approval"]["action"] in {"confirm", "cancel"}
    denied = await client.post(
        f"/api/v1/assistant/runs/{run_id}/decision", json={"approve": True}
    )
    assert denied.status_code == 403
    # Every request creates a new graph/checkpointer: resume is genuinely durable.
    accepted = await client.post(
        f"/api/v1/assistant/runs/{run_id}/decision",
        json={"approve": True},
        headers=REVIEWER,
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "completed"
    replay = await client.post(
        f"/api/v1/assistant/runs/{run_id}/decision",
        json={"approve": True},
        headers=REVIEWER,
    )
    assert replay.json() == accepted.json()
    assert (await client.get(f"/api/v1/orders/{order_id}")).json()["status"] == expected
    assert (await client.get(f"/api/v1/products/{product_id}")).json()["stock"] == (
        10 if expected == "cancelled" else 8
    )
    opposite = await client.post(
        f"/api/v1/assistant/runs/{run_id}/decision",
        json={"approve": False},
        headers=REVIEWER,
    )
    assert opposite.status_code == 409


async def test_rejection_keeps_order_unchanged(client):
    order_id, product_id = await pending_order(client)
    run_id = await request_action(client, order_id)
    response = await client.post(
        f"/api/v1/assistant/runs/{run_id}/decision",
        json={"approve": False},
        headers=REVIEWER,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert (await client.get(f"/api/v1/orders/{order_id}")).json()[
        "status"
    ] == "pending"
    assert (await client.get(f"/api/v1/products/{product_id}")).json()["stock"] == 8


async def test_expired_approval_is_not_executed(client, session):
    order_id, _ = await pending_order(client)
    run_id = await request_action(client, order_id)
    from uuid import UUID

    run = await session.get(AssistantRun, UUID(run_id))
    run.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await session.commit()
    response = await client.post(
        f"/api/v1/assistant/runs/{run_id}/decision",
        json={"approve": True},
        headers=REVIEWER,
    )
    assert response.status_code == 410
    assert (await client.get(f"/api/v1/orders/{order_id}")).json()[
        "status"
    ] == "pending"


async def test_changed_order_invalidates_preview(client):
    order_id, product_id = await pending_order(client)
    run_id = await request_action(client, order_id)
    changed = await client.post(f"/api/v1/orders/{order_id}/confirm", headers=REVIEWER)
    assert changed.status_code == 200
    response = await client.post(
        f"/api/v1/assistant/runs/{run_id}/decision",
        json={"approve": True},
        headers=REVIEWER,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "failed"
    assert (await client.get(f"/api/v1/products/{product_id}")).json()["stock"] == 8


async def test_concurrent_approvals_apply_action_once(client):
    order_id, product_id = await pending_order(client)
    run_id = await request_action(client, order_id)
    responses = await asyncio.gather(
        *[
            client.post(
                f"/api/v1/assistant/runs/{run_id}/decision",
                json={"approve": True},
                headers=REVIEWER,
            )
            for _ in range(2)
        ]
    )
    assert [response.status_code for response in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    assert (await client.get(f"/api/v1/products/{product_id}")).json()["stock"] == 10


async def test_protected_api_requires_credentials(client):
    response = await client.get("/api/v1/orders", headers={"Authorization": ""})
    assert response.status_code == 401
    response = await client.get(
        "/api/v1/orders", headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401
    response = await client.post("/api/v1/orders/1/cancel", headers=OPERATOR)
    assert response.status_code == 403


async def test_missing_order_and_ambiguous_action_do_not_pause(client):
    for question in ("Cancelar mi pedido", "Confirmar o cancelar la orden 1"):
        response = await client.post(
            "/api/v1/assistant/ask", json={"question": question}
        )
        assert response.status_code == 200, response.text
        assert response.json()["run_id"] is None


async def test_whitespace_question_rejected(client):
    response = await client.post("/api/v1/assistant/ask", json={"question": "   "})
    assert response.status_code == 422
