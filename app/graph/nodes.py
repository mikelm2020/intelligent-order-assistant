from app.graph.state import AssistantState
from app.services.rag import RAGService


class RAGNode:
    def __init__(self, rag_service: RAGService) -> None:
        self.rag_service = rag_service

    async def __call__(self, state: AssistantState) -> dict[str, str]:
        answer = await self.rag_service.answer(state["question"])

        return {"answer": answer}
