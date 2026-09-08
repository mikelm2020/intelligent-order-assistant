from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        title: str,
        content: str,
        source: str | None = None,
    ) -> Document:
        document = Document(
            title=title,
            content=content,
            source=source,
        )

        self.session.add(document)
        await self.session.flush()

        return document

    async def get_by_id(self, document_id: int) -> Document | None:
        statement = (
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.id == document_id)
        )

        return await self.session.scalar(statement)

    async def list(self) -> list[Document]:
        statement = (
            select(Document)
            .options(selectinload(Document.chunks))
            .order_by(Document.id)
        )

        result = await self.session.scalars(statement)
        return list(result.all())
