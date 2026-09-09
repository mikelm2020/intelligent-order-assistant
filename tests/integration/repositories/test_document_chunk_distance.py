import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import DocumentChunkRepository


@pytest.mark.asyncio
async def test_similarity_search_returns_ordered_distances(
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
        content="Resultado más cercano",
        embedding=[1.0, 0.0, 0.0] + [0.0] * 1533,
    )

    await chunk_repository.create(
        document_id=document.id,
        chunk_index=1,
        content="Resultado intermedio",
        embedding=[0.8, 0.6, 0.0] + [0.0] * 1533,
    )

    await chunk_repository.create(
        document_id=document.id,
        chunk_index=2,
        content="Resultado lejano",
        embedding=[0.0, 1.0, 0.0] + [0.0] * 1533,
    )

    await session.commit()

    results = await chunk_repository.similarity_search_with_distance(
        embedding=[1.0, 0.0, 0.0] + [0.0] * 1533,
        limit=3,
    )

    assert len(results) == 3

    chunks = [chunk for chunk, _ in results]
    distances = [distance for _, distance in results]

    assert [chunk.content for chunk in chunks] == [
        "Resultado más cercano",
        "Resultado intermedio",
        "Resultado lejano",
    ]

    assert distances == sorted(distances)

    assert distances[0] == pytest.approx(0.0)
    assert distances[1] == pytest.approx(0.2)
    assert distances[2] == pytest.approx(1.0)
