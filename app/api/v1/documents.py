from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.ai.embeddings import EmbeddingProvider
from app.ai.factory import get_embedding_provider
from app.core.database import SessionDep
from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import DocumentChunkRepository
from app.schemas.document import (
    DocumentChunkResponse,
    DocumentCreate,
    DocumentResponse,
    DocumentSearchRequest,
)
from app.services.document_ingestion import DocumentIngestionService
from app.services.document_retrieval import DocumentRetrievalService

EmbeddingProviderDep = Annotated[
    EmbeddingProvider,
    Depends(get_embedding_provider),
]

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    data: DocumentCreate,
    session: SessionDep,
    embedding_provider: EmbeddingProviderDep,
) -> DocumentResponse:
    service = DocumentIngestionService(
        document_repository=DocumentRepository(session),
        chunk_repository=DocumentChunkRepository(session),
        embedding_provider=embedding_provider,
    )

    document = await service.ingest(
        title=data.title,
        content=data.content,
        source=data.source,
    )

    await session.commit()
    await session.refresh(document)

    return DocumentResponse.model_validate(document)


@router.post(
    "/search",
    response_model=list[DocumentChunkResponse],
)
async def search_documents(
    data: DocumentSearchRequest,
    session: SessionDep,
    embedding_provider: EmbeddingProviderDep,
) -> list[DocumentChunkResponse]:
    service = DocumentRetrievalService(
        chunk_repository=DocumentChunkRepository(session),
        embedding_provider=embedding_provider,
    )

    chunks = await service.search(
        data.query,
        limit=data.limit,
    )

    return [DocumentChunkResponse.model_validate(chunk) for chunk in chunks]
