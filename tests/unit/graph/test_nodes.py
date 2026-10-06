from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.graph.nodes import OrderNode, RAGNode, RouterNode, extract_order_id


@pytest.mark.asyncio
async def test_rag_node_returns_answer() -> None:
    rag_service = AsyncMock()
    rag_service.answer.return_value = "Las devoluciones se aceptan en 30 días."

    node = RAGNode(rag_service)

    result = await node(
        {
            "question": "¿Cuál es la política de devoluciones?",
            "answer": "",
        }
    )

    rag_service.answer.assert_awaited_once_with("¿Cuál es la política de devoluciones?")
    assert result == {"answer": "Las devoluciones se aceptan en 30 días."}


@pytest.mark.asyncio
async def test_router_node_routes_order_question() -> None:
    node = RouterNode()

    result = await node(
        {
            "question": "Quiero consultar la orden 15",
            "answer": "",
            "intent": "knowledge",
            "order_id": None,
        }
    )

    assert result == {
        "intent": "order",
        "order_id": 15,
    }


@pytest.mark.asyncio
async def test_router_node_routes_knowledge_question() -> None:
    node = RouterNode()

    result = await node(
        {
            "question": "¿Cuál es la política de devoluciones?",
            "answer": "",
            "intent": "knowledge",
            "order_id": None,
        }
    )

    assert result == {
        "intent": "knowledge",
        "order_id": None,
    }


def test_extract_order_id_from_order_question() -> None:
    assert extract_order_id("Consulta la orden 15") == 15


def test_extract_order_id_with_hash() -> None:
    assert extract_order_id("Consulta la orden #27") == 27


def test_extract_order_id_from_pedido_question() -> None:
    assert extract_order_id("Quiero cancelar el pedido 8") == 8


def test_extract_order_id_returns_none_when_missing() -> None:
    assert extract_order_id("Quiero consultar mi pedido") is None


@pytest.mark.asyncio
async def test_order_node_requests_order_id_when_missing() -> None:
    order_service = AsyncMock()
    node = OrderNode(order_service)

    result = await node(
        {
            "question": "Quiero consultar mi orden",
            "answer": "",
            "intent": "order",
            "order_id": None,
        }
    )

    order_service.get_order.assert_not_awaited()
    assert result == {"answer": "Necesito el número de orden para poder consultarla."}


@pytest.mark.asyncio
async def test_order_node_returns_not_found() -> None:
    order_service = AsyncMock()
    order_service.get_order.return_value = None

    node = OrderNode(order_service)

    result = await node(
        {
            "question": "Consulta la orden 15",
            "answer": "",
            "intent": "order",
            "order_id": 15,
        }
    )

    order_service.get_order.assert_awaited_once_with(15)
    assert result == {"answer": "No encontré la orden 15."}


@pytest.mark.asyncio
async def test_order_node_returns_order_summary() -> None:
    order_service = AsyncMock()
    order_service.get_order.return_value = SimpleNamespace(
        id=15,
        status="pending",
        total=Decimal("1250.50"),
    )

    node = OrderNode(order_service)

    result = await node(
        {
            "question": "Consulta la orden 15",
            "answer": "",
            "intent": "order",
            "order_id": 15,
        }
    )

    order_service.get_order.assert_awaited_once_with(15)
    assert result == {"answer": "Orden 15: estado pending, total $1250.50."}
