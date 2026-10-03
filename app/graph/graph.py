from langgraph.graph import END, START, StateGraph

from app.graph.nodes import RAGNode
from app.graph.state import AssistantState
from app.services.rag import RAGService


def create_assistant_graph(rag_service: RAGService):
    builder = StateGraph(AssistantState)

    builder.add_node("rag", RAGNode(rag_service))

    builder.add_edge(START, "rag")
    builder.add_edge("rag", END)

    return builder.compile()
