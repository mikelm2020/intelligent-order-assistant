import re

from app.graph.state import AssistantState
from app.services.order import OrderService
from app.services.rag import RAGService


def extract_order_id(question: str) -> int | None:
    match = re.search(r"\b(?:orden|pedido)\s+#?(\d+)\b", question.lower())

    if match is None:
        return None

    return int(match.group(1))


class RAGNode:
    def __init__(self, rag_service: RAGService) -> None:
        self.rag_service = rag_service

    async def __call__(self, state: AssistantState) -> dict[str, str]:
        answer = await self.rag_service.answer(state["question"])

        return {"answer": answer}


class RouterNode:
    async def __call__(self, state: AssistantState) -> dict[str, str | int | None]:
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

        order_id = extract_order_id(question) if intent == "order" else None
        order_action = None

        if intent == "order":
            if "cancelar" in question:
                order_action = "cancel"
            elif "confirmar" in question:
                order_action = "confirm"
            else:
                order_action = "lookup"

        return {
            "intent": intent,
            "order_id": order_id,
            "order_action": order_action,
        }


class OrderNode:
    def __init__(self, order_service: OrderService) -> None:
        self.order_service = order_service

    async def __call__(self, state: AssistantState) -> dict[str, str]:
        order_id = state["order_id"]

        if order_id is None:
            return {"answer": "Necesito el número de orden para poder consultarla."}

        order = await self.order_service.get_order(order_id)

        if order is None:
            return {"answer": f"No encontré la orden {order_id}."}

        return {
            "answer": (
                f"Orden {order.id}: estado {order.status}, total ${order.total}."
            )
        }
