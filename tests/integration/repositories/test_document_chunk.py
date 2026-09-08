import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.document_chunk import DocumentChunkRepository


@pytest.mark.asyncio
async def test_similarity_search_returns_closest_chunk(
    session: AsyncSession,
):
    document = Document(
        title="Política de devoluciones",
        content="Documento de prueba",
        source="test",
    )

    session.add(document)
    await session.flush()

    repository = DocumentChunkRepository(session)

    await repository.create(
        document_id=document.id,
        chunk_index=0,
        content="Las devoluciones se aceptan dentro de 30 días.",
        embedding=[1.0, 0.0, 0.0] + [0.0] * 1533,
    )

    await repository.create(
        document_id=document.id,
        chunk_index=1,
        content="Los envíos tardan entre 3 y 5 días.",
        embedding=[0.0, 1.0, 0.0] + [0.0] * 1533,
    )

    await repository.create(
        document_id=document.id,
        chunk_index=2,
        content="Los métodos de pago incluyen tarjeta y transferencia.",
        embedding=[0.0, 0.0, 1.0] + [0.0] * 1533,
    )

    await session.commit()

    results = await repository.similarity_search(
        embedding=[1.0, 0.0, 0.0] + [0.0] * 1533,
        limit=2,
    )

    assert len(results) == 2
    assert results[0].content == ("Las devoluciones se aceptan dentro de 30 días.")
