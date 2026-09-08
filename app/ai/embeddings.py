from typing import Protocol


class EmbeddingProvider(Protocol):
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding for the given text."""
        ...
