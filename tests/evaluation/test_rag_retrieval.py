import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import DocumentChunkRepository
from app.services.document_retrieval import DocumentRetrievalService
from tests.evaluation.rag_retrieval_cases import RETRIEVAL_CASES

QUESTION_EMBEDDINGS = {
    "¿Cuántos días tengo para devolver un producto?": [1.0, 0.0, 0.0] + [0.0] * 1533,
    "¿Puedo regresar un producto después de comprarlo?": [1.0, 0.0, 0.0] + [0.0] * 1533,
    "¿Cuánto tarda en llegar mi pedido?": [0.0, 1.0, 0.0] + [0.0] * 1533,
    "¿Qué formas de pago aceptan?": [0.0, 0.0, 1.0] + [0.0] * 1533,
    "¿Los productos tienen garantía de cinco años?": [0.577, 0.577, 0.577]
    + [0.0] * 1533,
}


class EvaluationEmbeddingProvider:
    async def embed(self, text: str) -> list[float]:
        return QUESTION_EMBEDDINGS[text]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", RETRIEVAL_CASES)
async def test_rag_retrieval_cases(
    session: AsyncSession,
    case,
):
    document_repository = DocumentRepository(session)
    chunk_repository = DocumentChunkRepository(session)

    documents = {
        "devoluciones": (
            "Los clientes pueden devolver un producto dentro de 30 días.",
            [1.0, 0.0, 0.0] + [0.0] * 1533,
        ),
        "envios": (
            "Los pedidos se entregan normalmente entre 3 y 5 días hábiles.",
            [0.0, 1.0, 0.0] + [0.0] * 1533,
        ),
        "pagos": (
            "Aceptamos tarjeta de crédito, débito y transferencia bancaria.",
            [0.0, 0.0, 1.0] + [0.0] * 1533,
        ),
    }

    created_documents = {}

    for name, (content, embedding) in documents.items():
        document = await document_repository.create(
            title=name,
            content=content,
            source="evaluation",
        )

        await chunk_repository.create(
            document_id=document.id,
            chunk_index=0,
            content=content,
            embedding=embedding,
        )

        created_documents[document.id] = name

    await session.commit()

    service = DocumentRetrievalService(
        chunk_repository=chunk_repository,
        embedding_provider=EvaluationEmbeddingProvider(),
    )

    results = await service.search(
        case["question"],
        limit=1,
        max_distance=0.4,
    )

    expected_document = case["expected_document"]

    if expected_document is None:
        assert results == []
        return

    assert len(results) == 1

    result_document = created_documents[results[0].document_id]

    assert result_document == expected_document
