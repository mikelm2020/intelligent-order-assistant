from typing import Any, Literal, NotRequired, TypedDict


class AssistantState(TypedDict):
    question: str
    answer: str
    intent: Literal["knowledge", "order"]
    order_id: int | None
    order_action: Literal["lookup", "confirm", "cancel"] | None
    limit: NotRequired[int]
    max_distance: NotRequired[float | None]
    run_id: NotRequired[str]
    order_preview: NotRequired[dict[str, Any] | None]
    routing_error: NotRequired[str | None]
