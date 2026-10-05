from unittest.mock import AsyncMock

import pytest

from app.graph.graph import create_assistant_graph


@pytest.mark.asyncio
async def test_assistant_graph_routes_knowledge_to_rag() -> None:
    rag_service = AsyncMock()
    rag_service.answer.return_value = "Respuesta generada por RAG."

    graph = create_assistant_graph(rag_service)

    result = await graph.ainvoke(
        {
            "question": "¿Cuál es la política de devoluciones?",
            "answer": "",
            "intent": "knowledge",
        }
    )

    rag_service.answer.assert_awaited_once_with("¿Cuál es la política de devoluciones?")
    assert result["intent"] == "knowledge"
    assert result["answer"] == "Respuesta generada por RAG."


@pytest.mark.asyncio
async def test_assistant_graph_routes_order_without_calling_rag() -> None:
    rag_service = AsyncMock()

    graph = create_assistant_graph(rag_service)

    result = await graph.ainvoke(
        {
            "question": "Quiero cancelar mi pedido",
            "answer": "",
            "intent": "knowledge",
        }
    )

    rag_service.answer.assert_not_awaited()
    assert result["intent"] == "order"
    assert result["answer"] == ""
