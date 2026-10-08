from app.ai.demo import DemoEmbeddingProvider
from app.ai.embeddings import EmbeddingProvider
from app.ai.openai_embeddings import OpenAIEmbeddingProvider
from app.core.config import settings


def get_embedding_provider() -> EmbeddingProvider:
    if settings.ai_provider == "demo":
        return DemoEmbeddingProvider()
    return OpenAIEmbeddingProvider()
