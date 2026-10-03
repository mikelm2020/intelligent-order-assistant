from unittest.mock import AsyncMock

import pytest

from app.graph.nodes import RAGNode


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
