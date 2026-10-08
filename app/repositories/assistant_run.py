from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assistant_run import AssistantRun


class AssistantRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **values) -> AssistantRun:
        run = AssistantRun(**values)
        self.session.add(run)
        await self.session.flush()
        return run

    async def get(self, run_id: UUID, *, lock: bool = False) -> AssistantRun | None:
        query = select(AssistantRun).where(AssistantRun.id == run_id)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(query)
