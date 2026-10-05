from unittest.mock import AsyncMock

import pytest

from app.graph.nodes import RAGNode, RouterNode


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
            "question": "Quiero cancelar mi pedido",
            "answer": "",
            "intent": "knowledge",
        }
    )

    assert result == {"intent": "order"}


@pytest.mark.asyncio
async def test_router_node_routes_knowledge_question() -> None:
    node = RouterNode()

    result = await node(
        {
            "question": "¿Cuál es la política de devoluciones?",
            "answer": "",
            "intent": "knowledge",
        }
    )

    assert result == {"intent": "knowledge"}
