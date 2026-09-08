from fastapi import APIRouter, status

from app.ai.factory import get_embedding_provider
from app.core.database import SessionDep
from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import DocumentChunkRepository
from app.schemas.document import DocumentCreate, DocumentResponse
from app.services.document_ingestion import DocumentIngestionService

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
) -> DocumentResponse:
    service = DocumentIngestionService(
        document_repository=DocumentRepository(session),
        chunk_repository=DocumentChunkRepository(session),
        embedding_provider=get_embedding_provider(),
    )

    document = await service.ingest(
        title=data.title,
        content=data.content,
        source=data.source,
    )

    await session.commit()
    await session.refresh(document)

    return DocumentResponse.model_validate(document)
