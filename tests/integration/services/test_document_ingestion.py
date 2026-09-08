import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import DocumentChunkRepository
from app.services.document_ingestion import DocumentIngestionService
from tests.fakes.embedding_provider import FakeEmbeddingProvider


@pytest.mark.asyncio
async def test_ingest_creates_document_and_chunks(
    session: AsyncSession,
):
    service = DocumentIngestionService(
        document_repository=DocumentRepository(session),
        chunk_repository=DocumentChunkRepository(session),
        embedding_provider=FakeEmbeddingProvider(),
        chunk_size=10,
        chunk_overlap=2,
    )

    document = await service.ingest(
        title="Política de devoluciones",
        content="abcdefghijklmnopqrst",
        source="test",
    )

    await session.commit()

    stored_document = await session.get(Document, document.id)

    result = await session.scalars(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document.id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = list(result.all())

    assert stored_document is not None
    assert stored_document.title == "Política de devoluciones"
    assert stored_document.source == "test"

    assert len(chunks) == 3

    assert [chunk.content for chunk in chunks] == [
        "abcdefghij",
        "ijklmnopqr",
        "qrst",
    ]

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]

    assert all(chunk.embedding is not None for chunk in chunks)
