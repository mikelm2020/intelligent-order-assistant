from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RAGQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=5, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def nonempty_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question cannot be empty")
        return value.strip()


class RAGAnswerResponse(BaseModel):
    answer: str
    run_id: UUID | None = None
    status: Literal[
        "completed", "pending_approval", "rejected", "failed", "expired"
    ] = "completed"
    approval: dict[str, Any] | None = None


class ApprovalDecision(BaseModel):
    approve: bool = Field(strict=True)
