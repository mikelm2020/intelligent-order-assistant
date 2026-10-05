from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import RAGNode, RouterNode
from app.graph.state import AssistantState
from app.services.rag import RAGService


def route_intent(
    state: AssistantState,
) -> Literal["rag", "order"]:
    if state["intent"] == "order":
        return "order"

    return "rag"


def create_assistant_graph(rag_service: RAGService):
    builder = StateGraph(AssistantState)

    builder.add_node("router", RouterNode())
    builder.add_node("rag", RAGNode(rag_service))

    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        route_intent,
        {
            "rag": "rag",
            "order": END,
        },
    )

    builder.add_edge("rag", END)

    return builder.compile()
