from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.graph.graph import create_assistant_graph


@pytest.mark.asyncio
async def test_assistant_graph_routes_knowledge_to_rag() -> None:
    rag_service = AsyncMock()
    rag_service.answer.return_value = "Respuesta generada por RAG."
    order_service = AsyncMock()

    graph = create_assistant_graph(rag_service, order_service)

    result = await graph.ainvoke(
        {
            "question": "¿Cuál es la política de devoluciones?",
            "answer": "",
            "intent": "knowledge",
            "order_id": None,
            "order_action": None,
        }
    )

    rag_service.answer.assert_awaited_once_with("¿Cuál es la política de devoluciones?")
    order_service.get_order.assert_not_awaited()

    assert result["order_action"] is None
    assert result["intent"] == "knowledge"
    assert result["order_id"] is None
    assert result["answer"] == "Respuesta generada por RAG."


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("question", "order_action"),
    [
        ("Quiero consultar la orden 15", "lookup"),
        ("Quiero confirmar la orden 15", "confirm"),
        ("Quiero cancelar la orden 15", "cancel"),
    ],
)
async def test_assistant_graph_routes_order_to_order_node(
    question: str, order_action: str
) -> None:
    rag_service = AsyncMock()
    order_service = AsyncMock()
    order_service.get_order.return_value = SimpleNamespace(
        id=15,
        status="pending",
        total=Decimal("1250.50"),
    )

    graph = create_assistant_graph(rag_service, order_service)

    result = await graph.ainvoke(
        {
            "question": question,
            "answer": "",
            "intent": "knowledge",
            "order_id": None,
            "order_action": None,
        }
    )

    rag_service.answer.assert_not_awaited()
    order_service.get_order.assert_awaited_once_with(15)
    order_service.confirm_order.assert_not_awaited()
    order_service.cancel_order.assert_not_awaited()

    assert result["order_action"] == order_action
    assert result["intent"] == "order"
    assert result["order_id"] == 15
    assert result["answer"] == ("Orden 15: estado pending, total $1250.50.")
