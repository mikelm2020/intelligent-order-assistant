from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_embedding_provider
from app.main import app
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


@pytest.fixture
def mock_embedding_provider():
    provider = AsyncMock()

    provider.embed.return_value = [1.0, 0.0, 0.0] + [0.0] * 1533

    app.dependency_overrides[get_embedding_provider] = lambda: provider

    yield provider

    app.dependency_overrides.pop(get_embedding_provider, None)


@pytest.mark.asyncio
async def test_search_documents_returns_most_similar_chunk(
    client,
    session: AsyncSession,
    mock_embedding_provider,
):
    document = Document(
        title="Políticas",
        content="Documento de prueba",
        source="test",
    )

    session.add(document)
    await session.flush()

    session.add_all(
        [
            DocumentChunk(
                document_id=document.id,
                chunk_index=0,
                content="Las devoluciones se aceptan dentro de 30 días.",
                embedding=[1.0, 0.0, 0.0] + [0.0] * 1533,
            ),
            DocumentChunk(
                document_id=document.id,
                chunk_index=1,
                content="Los envíos tardan entre 3 y 5 días.",
                embedding=[0.0, 1.0, 0.0] + [0.0] * 1533,
            ),
        ]
    )

    await session.commit()

    response = await client.post(
        "/api/v1/documents/search",
        json={
            "query": "¿Cuál es la política de devoluciones?",
            "limit": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["content"] == ("Las devoluciones se aceptan dentro de 30 días.")

    mock_embedding_provider.embed.assert_awaited_once_with(
        "¿Cuál es la política de devoluciones?"
    )
