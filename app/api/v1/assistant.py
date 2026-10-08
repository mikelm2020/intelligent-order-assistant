from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.ai.chat import ChatProvider
from app.ai.chat_factory import get_chat_provider
from app.ai.embeddings import EmbeddingProvider
from app.ai.factory import get_embedding_provider
from app.core.database import SessionDep
from app.core.security import PrincipalDep, ReviewerDep
from app.exceptions.assistant import WorkflowError
from app.graph.checkpointer import get_checkpointer
from app.repositories.document_chunk import DocumentChunkRepository
from app.schemas.rag import ApprovalDecision, RAGAnswerResponse, RAGQuestionRequest
from app.services.assistant import AssistantService
from app.services.document_retrieval import DocumentRetrievalService
from app.services.rag import RAGService

router = APIRouter(prefix="/assistant", tags=["assistant"])
EmbeddingProviderDep = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
ChatProviderDep = Annotated[ChatProvider, Depends(get_chat_provider)]
CheckpointerDep = Annotated[object, Depends(get_checkpointer)]


# Lazy construction avoids requiring an OpenAI key for order-only workflows.
class LazyEmbeddingProvider:
    async def embed(self, text: str) -> list[float]:
        return await get_embedding_provider().embed(text)


class LazyChatProvider:
    async def generate(self, *, question: str, context: str) -> str:
        return await get_chat_provider().generate(question=question, context=context)


def get_assistant_embedding_provider() -> EmbeddingProvider:
    return LazyEmbeddingProvider()


def get_assistant_chat_provider() -> ChatProvider:
    return LazyChatProvider()


def get_assistant_service(
    session: SessionDep,
    checkpointer: CheckpointerDep,
    embedding_provider: Annotated[
        EmbeddingProvider, Depends(get_assistant_embedding_provider)
    ],
    chat_provider: Annotated[ChatProvider, Depends(get_assistant_chat_provider)],
) -> AssistantService:
    retrieval = DocumentRetrievalService(
        DocumentChunkRepository(session), embedding_provider
    )
    return AssistantService(session, RAGService(retrieval, chat_provider), checkpointer)


AssistantDep = Annotated[AssistantService, Depends(get_assistant_service)]


@router.post("/ask", response_model=RAGAnswerResponse)
async def ask_assistant(
    data: RAGQuestionRequest, principal: PrincipalDep, service: AssistantDep
):
    return await service.ask(data.question, data.limit, principal.role)


@router.get("/runs/{run_id}", response_model=RAGAnswerResponse)
async def get_run(run_id: UUID, service: AssistantDep):
    try:
        return await service.review(run_id)
    except WorkflowError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


@router.post("/runs/{run_id}/decision", response_model=RAGAnswerResponse)
async def decide_run(
    run_id: UUID, data: ApprovalDecision, reviewer: ReviewerDep, service: AssistantDep
):
    try:
        return await service.decide(run_id, data.approve, reviewer.role)
    except WorkflowError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
