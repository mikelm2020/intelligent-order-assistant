import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import DocumentChunkRepository


@pytest.mark.asyncio
async def test_vector_distance_separates_relevant_and_irrelevant_chunks(
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
        content="Información relevante",
        embedding=[1.0, 0.0, 0.0] + [0.0] * 1533,
    )

    await chunk_repository.create(
        document_id=document.id,
        chunk_index=1,
        content="Información parcialmente relevante",
        embedding=[0.8, 0.6, 0.0] + [0.0] * 1533,
    )

    await chunk_repository.create(
        document_id=document.id,
        chunk_index=2,
        content="Información irrelevante",
        embedding=[0.0, 1.0, 0.0] + [0.0] * 1533,
    )

    await session.commit()

    results = await chunk_repository.similarity_search_with_distance(
        embedding=[1.0, 0.0, 0.0] + [0.0] * 1533,
        limit=3,
    )

    assert len(results) == 3

    assert results[0][0].content == "Información relevante"
    assert results[0][1] == pytest.approx(0.0)

    assert results[1][0].content == "Información parcialmente relevante"
    assert results[1][1] == pytest.approx(0.2)

    assert results[2][0].content == "Información irrelevante"
    assert results[2][1] == pytest.approx(1.0)
