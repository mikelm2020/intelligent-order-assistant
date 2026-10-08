import re

from langgraph.types import interrupt

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
        kwargs = {}
        if "limit" in state:
            kwargs["limit"] = state["limit"]
        if "max_distance" in state:
            kwargs["max_distance"] = state["max_distance"]
        answer = await self.rag_service.answer(state["question"], **kwargs)

        return {"answer": answer}


class RouterNode:
    async def __call__(self, state: AssistantState) -> dict[str, str | int | None]:
        question = state["question"].lower()

        order_id = extract_order_id(question)
        cancel = bool(re.search(r"\bcancelar\b", question))
        confirm = bool(re.search(r"\bconfirmar\b", question))
        lookup = bool(
            re.search(r"\b(?:consultar|consulta|estado|orden|pedido)\b", question)
        )
        order_reference = bool(re.search(r"\b(?:orden|pedido)\b", question))
        explicit_lookup = (
            lookup
            and order_reference
            and (
                bool(re.search(r"\b(?:consultar|consulta|estado)\b", question))
                or question.strip().startswith(
                    ("orden", "pedido", "mi orden", "mi pedido")
                )
            )
        )
        intent = (
            "order"
            if order_id is not None or cancel or confirm or explicit_lookup
            else "knowledge"
        )
        order_action = None
        if intent == "order":
            order_action = "cancel" if cancel else "confirm" if confirm else "lookup"
        result = {
            "intent": intent,
            "order_id": order_id if intent == "order" else None,
            "order_action": order_action,
        }
        if (cancel and confirm) or (
            (cancel or confirm) and re.search(r"\bno\b", question)
        ):
            result["routing_error"] = (
                "Especifica una sola acción afirmativa para la orden."
            )
        return result


class OrderNode:
    def __init__(self, order_service: OrderService) -> None:
        self.order_service = order_service

    async def __call__(self, state: AssistantState) -> dict[str, str]:
        if state.get("routing_error"):
            return {"answer": state["routing_error"], "order_preview": None}

        order_id = state["order_id"]

        if order_id is None:
            return {"answer": "Necesito el número de orden para poder consultarla."}

        order = await self.order_service.get_order(order_id)

        if order is None:
            return {"answer": f"No encontré la orden {order_id}."}

        if state.get("order_action") in {"confirm", "cancel"}:
            if order.status != "pending":
                return {
                    "answer": "La orden ya no está pendiente; no se solicitó una acción.",
                    "order_preview": None,
                }
            return {
                "answer": "Aprobación requerida.",
                "order_preview": {
                    "order_id": order.id,
                    "action": state["order_action"],
                    "status": order.status,
                    "total": str(order.total),
                    "updated_at": order.updated_at.isoformat(),
                },
            }

        return {
            "answer": (
                f"Orden {order.id}: estado {order.status}, total ${order.total}."
            )
        }


class ApprovalNode:
    def __init__(self, action_executor) -> None:
        self.action_executor = action_executor

    async def __call__(self, state: AssistantState) -> dict[str, str]:
        approved = interrupt(state["order_preview"])
        if approved is not True:
            return {"answer": "Acción rechazada; la orden no fue modificada."}
        if self.action_executor is None:
            return {"answer": "La ejecución de acciones no está configurada."}
        return {"answer": await self.action_executor(state["run_id"])}
