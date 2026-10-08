from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.graph.graph import create_assistant_graph


def state(question: str) -> dict:
    return {
        "question": question,
        "answer": "",
        "intent": "knowledge",
        "order_id": None,
        "order_action": None,
        "run_id": "test-run",
    }


def order_service():
    service = AsyncMock()
    service.get_order.return_value = SimpleNamespace(
        id=15,
        status="pending",
        total=Decimal("1250.50"),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    return service


@pytest.mark.asyncio
async def test_assistant_graph_routes_knowledge_to_rag() -> None:
    rag = AsyncMock()
    rag.answer.return_value = "Respuesta generada por RAG."
    orders = order_service()
    graph = create_assistant_graph(rag, orders)
    result = await graph.ainvoke(state("¿Cuál es la política de devoluciones?"))
    rag.answer.assert_awaited_once_with("¿Cuál es la política de devoluciones?")
    orders.get_order.assert_not_awaited()
    assert result["order_action"] is None
    assert result["answer"] == "Respuesta generada por RAG."


@pytest.mark.asyncio
async def test_graph_preserves_rag_policy() -> None:
    rag = AsyncMock()
    graph = create_assistant_graph(rag, order_service())
    initial = state("¿Qué formas de pago aceptan?") | {"limit": 3, "max_distance": 0.25}
    await graph.ainvoke(initial)
    rag.answer.assert_awaited_once_with(initial["question"], limit=3, max_distance=0.25)


@pytest.mark.asyncio
async def test_assistant_graph_routes_lookup_to_order_node() -> None:
    rag = AsyncMock()
    orders = order_service()
    result = await create_assistant_graph(rag, orders).ainvoke(
        state("Consulta la orden 15")
    )
    rag.answer.assert_not_awaited()
    orders.get_order.assert_awaited_once_with(15)
    orders.confirm_order.assert_not_awaited()
    orders.cancel_order.assert_not_awaited()
    assert result["order_action"] == "lookup"
    assert result["answer"] == "Orden 15: estado pending, total $1250.50."


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["confirmar", "cancelar"])
@pytest.mark.parametrize("approve", [True, False])
async def test_graph_interrupts_before_action_and_resumes(action, approve) -> None:
    executor = AsyncMock(return_value="Acción ejecutada.")
    orders = order_service()
    graph = create_assistant_graph(
        AsyncMock(), orders, checkpointer=InMemorySaver(), action_executor=executor
    )
    config = {"configurable": {"thread_id": "test-run"}}
    result = await graph.ainvoke(state(f"Quiero {action} la orden 15"), config)
    assert result["__interrupt__"][0].value["order_id"] == 15
    assert result["__interrupt__"][0].value["total"] == "1250.50"
    executor.assert_not_awaited()
    orders.confirm_order.assert_not_awaited()
    orders.cancel_order.assert_not_awaited()
    result = await graph.ainvoke(Command(resume=approve), config)
    if approve:
        executor.assert_awaited_once_with("test-run")
        assert result["answer"] == "Acción ejecutada."
    else:
        executor.assert_not_awaited()
        assert "rechazada" in result["answer"]


@pytest.mark.asyncio
async def test_graph_missing_order_does_not_request_approval() -> None:
    executor = AsyncMock()
    graph = create_assistant_graph(
        AsyncMock(),
        order_service(),
        checkpointer=InMemorySaver(),
        action_executor=executor,
    )
    result = await graph.ainvoke(
        state("Quiero cancelar mi pedido"), {"configurable": {"thread_id": "missing"}}
    )
    assert "__interrupt__" not in result
    executor.assert_not_awaited()
    assert "número de orden" in result["answer"]
