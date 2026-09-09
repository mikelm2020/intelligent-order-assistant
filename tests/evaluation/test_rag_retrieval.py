import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import DocumentChunkRepository
from app.services.document_retrieval import DocumentRetrievalService
from tests.evaluation.rag_retrieval_cases import RETRIEVAL_CASES
from tests.evaluation.rag_retrieval_metrics import (
    calculate_retrieval_metrics,
)

QUESTION_EMBEDDINGS = {
    "¿Cuántos días tengo para devolver un producto?": [1.0, 0.0, 0.0] + [0.0] * 1533,
    "¿Puedo regresar un producto después de comprarlo?": [1.0, 0.0, 0.0] + [0.0] * 1533,
    "¿Cuánto tarda en llegar mi pedido?": [0.0, 1.0, 0.0] + [0.0] * 1533,
    "¿Qué formas de pago aceptan?": [0.0, 0.0, 1.0] + [0.0] * 1533,
    "¿Los productos tienen garantía de cinco años?": [0.577, 0.577, 0.577]
    + [0.0] * 1533,
}


DOCUMENTS = {
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


class EvaluationEmbeddingProvider:
    async def embed(self, text: str) -> list[float]:
        return QUESTION_EMBEDDINGS[text]


async def evaluate_retrieval_case(
    *,
    session: AsyncSession,
    case,
) -> bool:
    document_repository = DocumentRepository(session)
    chunk_repository = DocumentChunkRepository(session)

    created_documents = {}

    for name, (content, embedding) in DOCUMENTS.items():
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
        return results == []

    if len(results) != 1:
        return False

    result_document = created_documents[results[0].document_id]

    return result_document == expected_document


@pytest.mark.asyncio
@pytest.mark.parametrize("case", RETRIEVAL_CASES)
async def test_rag_retrieval_cases(
    session: AsyncSession,
    case,
):
    result = await evaluate_retrieval_case(
        session=session,
        case=case,
    )

    assert result is True


@pytest.mark.asyncio
async def test_rag_retrieval_evaluation_metrics(
    session: AsyncSession,
):
    document_repository = DocumentRepository(session)
    chunk_repository = DocumentChunkRepository(session)

    created_documents = {}

    for name, (content, embedding) in DOCUMENTS.items():
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

    results = []

    for case in RETRIEVAL_CASES:
        retrieved_chunks = await service.search(
            case["question"],
            limit=1,
            max_distance=0.4,
        )

        expected_document = case["expected_document"]

        if expected_document is None:
            results.append(retrieved_chunks == [])
            continue

        if len(retrieved_chunks) != 1:
            results.append(False)
            continue

        result_document = created_documents[retrieved_chunks[0].document_id]

        results.append(result_document == expected_document)

    metrics = calculate_retrieval_metrics(results)

    assert metrics.total_cases == 5
    assert metrics.correct_cases == 5
    assert metrics.accuracy == pytest.approx(1.0)
