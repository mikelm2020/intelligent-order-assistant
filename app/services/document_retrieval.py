from app.ai.embeddings import EmbeddingProvider
from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk import DocumentChunkRepository


class DocumentRetrievalService:
    def __init__(
        self,
        chunk_repository: DocumentChunkRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.chunk_repository = chunk_repository
        self.embedding_provider = embedding_provider

    async def search(
        self,
        query: str,
        *,
        limit: int = 5,
        max_distance: float | None = None,
    ) -> list[DocumentChunk]:
        query = query.strip()

        if not query:
            return []

        embedding = await self.embedding_provider.embed(query)

        if max_distance is None:
            return await self.chunk_repository.similarity_search(
                embedding=embedding,
                limit=limit,
            )

        results = await self.chunk_repository.similarity_search_with_distance(
            embedding=embedding,
            limit=limit,
        )

        return [chunk for chunk, distance in results if distance <= max_distance]
