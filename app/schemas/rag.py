from pydantic import BaseModel, Field


class RAGQuestionRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
    max_distance: float = Field(default=0.4, ge=0.0, le=2.0)


class RAGAnswerResponse(BaseModel):
    answer: str
