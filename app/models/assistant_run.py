from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin


class AssistantRun(TimestampMixin, Base):
    __tablename__ = "assistant_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    requested_by: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    preview: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    answer: Mapped[str | None] = mapped_column(nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(30), nullable=True)
    decision: Mapped[bool | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
