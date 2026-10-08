from openai import AsyncOpenAI

from app.core.config import settings
from app.exceptions.ai import AIConfigurationError


class OpenAIEmbeddingProvider:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise AIConfigurationError("AI provider credentials are not configured")

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
        )

        self.model = settings.openai_embedding_model

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=1536,
        )

        return response.data[0].embedding
