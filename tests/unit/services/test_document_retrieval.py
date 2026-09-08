from unittest.mock import AsyncMock

import pytest

from app.services.document_retrieval import DocumentRetrievalService


class FakeEmbeddingProvider:
    async def embed(self, text: str) -> list[float]:
        return [1.0] + [0.0] * 1535


@pytest.mark.asyncio
async def test_search_returns_chunks_from_repository():
    chunk_repository = AsyncMock()

    expected_chunks = [
        object(),
        object(),
    ]

    chunk_repository.similarity_search.return_value = expected_chunks

    service = DocumentRetrievalService(
        chunk_repository=chunk_repository,
        embedding_provider=FakeEmbeddingProvider(),
    )

    result = await service.search(
        "¿Cuál es la política de devoluciones?",
        limit=3,
    )

    assert result == expected_chunks

    chunk_repository.similarity_search.assert_awaited_once_with(
        embedding=[1.0] + [0.0] * 1535,
        limit=3,
    )


@pytest.mark.asyncio
async def test_search_returns_empty_list_for_empty_query():
    chunk_repository = AsyncMock()

    service = DocumentRetrievalService(
        chunk_repository=chunk_repository,
        embedding_provider=FakeEmbeddingProvider(),
    )

    result = await service.search("   ")

    assert result == []
    chunk_repository.similarity_search.assert_not_awaited()
