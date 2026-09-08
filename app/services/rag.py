from app.ai.chat import ChatProvider
from app.services.document_retrieval import DocumentRetrievalService


class RAGService:
    def __init__(
        self,
        retrieval_service: DocumentRetrievalService,
        chat_provider: ChatProvider,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.chat_provider = chat_provider

    async def answer(
        self,
        question: str,
        *,
        limit: int = 5,
    ) -> str:
        question = question.strip()

        if not question:
            raise ValueError("question cannot be empty")

        chunks = await self.retrieval_service.search(
            question,
            limit=limit,
        )

        context = "\n\n".join(chunk.content for chunk in chunks)

        return await self.chat_provider.generate(
            question=question,
            context=context,
        )
