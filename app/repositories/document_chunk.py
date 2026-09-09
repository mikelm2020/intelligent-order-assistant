from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk


class DocumentChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        document_id: int,
        chunk_index: int,
        content: str,
        embedding: list[float] | None = None,
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
        )

        self.session.add(chunk)
        await self.session.flush()

        return chunk

    async def similarity_search(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.embedding.is_not(None))
            .order_by(DocumentChunk.embedding.cosine_distance(embedding))
            .limit(limit)
        )

        result = await self.session.scalars(statement)
        return list(result.all())

    async def similarity_search_with_distance(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> list[tuple[DocumentChunk, float]]:
        distance = DocumentChunk.embedding.cosine_distance(embedding).label("distance")

        statement = (
            select(
                DocumentChunk,
                distance,
            )
            .where(DocumentChunk.embedding.is_not(None))
            .order_by(distance)
            .limit(limit)
        )

        result = await self.session.execute(statement)

        return [
            (chunk, float(distance_value)) for chunk, distance_value in result.all()
        ]
