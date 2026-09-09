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
        max_distance: float | None = None,
    ) -> str:
        question = question.strip()

        if not question:
            raise ValueError("question cannot be empty")

        chunks = await self.retrieval_service.search(
            question,
            limit=limit,
            max_distance=max_distance,
        )

        if not chunks:
            return (
                "No tengo información suficiente en la documentación "
                "disponible para responder esa pregunta."
            )

        context = "\n\n".join(chunk.content for chunk in chunks)

        return await self.chat_provider.generate(
            question=question,
            context=context,
        )
