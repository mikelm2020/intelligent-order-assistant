from typing import Literal, TypedDict


class AssistantState(TypedDict):
    question: str
    answer: str
    intent: Literal["knowledge", "order"]
    order_id: int | None
    order_action: Literal["lookup", "confirm", "cancel"] | None
