from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import ApprovalNode, OrderNode, RAGNode, RouterNode
from app.graph.state import AssistantState
from app.services.order import OrderService
from app.services.rag import RAGService


def route_intent(
    state: AssistantState,
) -> Literal["rag", "order"]:
    if state["intent"] == "order":
        return "order"

    return "rag"


def create_assistant_graph(
    rag_service: RAGService,
    order_service: OrderService,
    *,
    checkpointer=None,
    action_executor=None,
):
    builder = StateGraph(AssistantState)

    builder.add_node("router", RouterNode())
    builder.add_node("rag", RAGNode(rag_service))
    builder.add_node("order", OrderNode(order_service))
    builder.add_node("approval", ApprovalNode(action_executor))

    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        route_intent,
        {
            "rag": "rag",
            "order": "order",
        },
    )

    builder.add_edge("rag", END)
    builder.add_conditional_edges(
        "order",
        lambda state: "approval" if state.get("order_preview") else "end",
        {"approval": "approval", "end": END},
    )
    builder.add_edge("approval", END)

    return builder.compile(checkpointer=checkpointer)
