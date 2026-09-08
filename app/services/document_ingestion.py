from app.ai.embeddings import EmbeddingProvider
from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import DocumentChunkRepository


class DocumentIngestionService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        chunk_repository: DocumentChunkRepository,
        embedding_provider: EmbeddingProvider,
        *,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.embedding_provider = embedding_provider
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        text = text.strip()

        if not text:
            return []

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            start = end - self.chunk_overlap

        return chunks

    async def ingest(
        self,
        *,
        title: str,
        content: str,
        source: str | None = None,
    ):
        chunks = self.split_text(content)

        if not chunks:
            raise ValueError("document content cannot be empty")

        document = await self.document_repository.create(
            title=title,
            content=content,
            source=source,
        )

        for index, chunk_content in enumerate(chunks):
            embedding = await self.embedding_provider.embed(chunk_content)

            await self.chunk_repository.create(
                document_id=document.id,
                chunk_index=index,
                content=chunk_content,
                embedding=embedding,
            )

        return document
