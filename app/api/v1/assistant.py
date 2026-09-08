from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.chat import ChatProvider
from app.ai.chat_factory import get_chat_provider
from app.ai.embeddings import EmbeddingProvider
from app.ai.factory import get_embedding_provider
from app.core.database import SessionDep
from app.repositories.document_chunk import DocumentChunkRepository
from app.schemas.rag import RAGAnswerResponse, RAGQuestionRequest
from app.services.document_retrieval import DocumentRetrievalService
from app.services.rag import RAGService

router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
)

EmbeddingProviderDep = Annotated[
    EmbeddingProvider,
    Depends(get_embedding_provider),
]

ChatProviderDep = Annotated[
    ChatProvider,
    Depends(get_chat_provider),
]


@router.post(
    "/ask",
    response_model=RAGAnswerResponse,
)
async def ask_assistant(
    data: RAGQuestionRequest,
    session: SessionDep,
    embedding_provider: EmbeddingProviderDep,
    chat_provider: ChatProviderDep,
) -> RAGAnswerResponse:
    retrieval_service = DocumentRetrievalService(
        chunk_repository=DocumentChunkRepository(session),
        embedding_provider=embedding_provider,
    )

    rag_service = RAGService(
        retrieval_service=retrieval_service,
        chat_provider=chat_provider,
    )

    answer = await rag_service.answer(
        data.question,
        limit=data.limit,
    )

    return RAGAnswerResponse(answer=answer)
