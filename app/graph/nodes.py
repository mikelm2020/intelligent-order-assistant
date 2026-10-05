from app.graph.state import AssistantState
from app.services.rag import RAGService


class RAGNode:
    def __init__(self, rag_service: RAGService) -> None:
        self.rag_service = rag_service

    async def __call__(self, state: AssistantState) -> dict[str, str]:
        answer = await self.rag_service.answer(state["question"])

        return {"answer": answer}


class RouterNode:
    async def __call__(self, state: AssistantState) -> dict[str, str]:
        question = state["question"].lower()

        order_keywords = (
            "orden",
            "pedido",
            "cancelar",
            "confirmar",
        )

        intent = (
            "order"
            if any(keyword in question for keyword in order_keywords)
            else "knowledge"
        )

        return {"intent": intent}
