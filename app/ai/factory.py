from app.ai.embeddings import EmbeddingProvider
from app.ai.openai_embeddings import OpenAIEmbeddingProvider


def get_embedding_provider() -> EmbeddingProvider:
    return OpenAIEmbeddingProvider()
