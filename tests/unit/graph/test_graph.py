from unittest.mock import AsyncMock

import pytest

from app.graph.graph import create_assistant_graph


@pytest.mark.asyncio
async def test_assistant_graph_executes_rag_node() -> None:
    rag_service = AsyncMock()
    rag_service.answer.return_value = "Respuesta generada por RAG."

    graph = create_assistant_graph(rag_service)

    result = await graph.ainvoke(
        {
            "question": "¿Cuál es la política de devoluciones?",
            "answer": "",
        }
    )

    rag_service.answer.assert_awaited_once_with("¿Cuál es la política de devoluciones?")
    assert result["question"] == "¿Cuál es la política de devoluciones?"
    assert result["answer"] == "Respuesta generada por RAG."
