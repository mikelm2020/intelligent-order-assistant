import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import DocumentChunkRepository
from app.services.document_retrieval import DocumentRetrievalService


class FakeEmbeddingProvider:
    async def embed(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0] + [0.0] * 1533


@pytest.mark.asyncio
async def test_search_returns_most_similar_chunk(
    session: AsyncSession,
):
    document_repository = DocumentRepository(session)
    chunk_repository = DocumentChunkRepository(session)

    document = await document_repository.create(
        title="Políticas",
        content="Documento de prueba",
        source="test",
    )

    await chunk_repository.create(
        document_id=document.id,
        chunk_index=0,
        content="Las devoluciones se aceptan dentro de 30 días.",
        embedding=[1.0, 0.0, 0.0] + [0.0] * 1533,
    )

    await chunk_repository.create(
        document_id=document.id,
        chunk_index=1,
        content="Los envíos tardan entre 3 y 5 días.",
        embedding=[0.0, 1.0, 0.0] + [0.0] * 1533,
    )

    await session.commit()

    service = DocumentRetrievalService(
        chunk_repository=chunk_repository,
        embedding_provider=FakeEmbeddingProvider(),
    )

    results = await service.search(
        "¿Cuál es la política de devoluciones?",
        limit=1,
    )

    assert len(results) == 1
    assert results[0].content == ("Las devoluciones se aceptan dentro de 30 días.")


@pytest.mark.asyncio
async def test_search_filters_chunks_by_max_distance(
    session: AsyncSession,
):
    document_repository = DocumentRepository(session)
    chunk_repository = DocumentChunkRepository(session)

    document = await document_repository.create(
        title="Políticas",
        content="Documento de prueba",
        source="test",
    )

    await chunk_repository.create(
        document_id=document.id,
        chunk_index=0,
        content="Resultado relevante",
        embedding=[1.0, 0.0, 0.0] + [0.0] * 1533,
    )

    await chunk_repository.create(
        document_id=document.id,
        chunk_index=1,
        content="Resultado irrelevante",
        embedding=[0.0, 1.0, 0.0] + [0.0] * 1533,
    )

    await session.commit()

    service = DocumentRetrievalService(
        chunk_repository=chunk_repository,
        embedding_provider=FakeEmbeddingProvider(),
    )

    results = await service.search(
        "¿Cuál es la política?",
        limit=5,
        max_distance=0.4,
    )

    assert len(results) == 1
    assert results[0].content == "Resultado relevante"
