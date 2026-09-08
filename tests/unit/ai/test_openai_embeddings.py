from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.openai_embeddings import OpenAIEmbeddingProvider


@pytest.mark.asyncio
async def test_embed_returns_embedding(monkeypatch):
    provider = OpenAIEmbeddingProvider()

    expected_embedding = [0.1] * 1536

    response = MagicMock()
    response.data = [
        MagicMock(embedding=expected_embedding),
    ]

    create_mock = AsyncMock(return_value=response)

    monkeypatch.setattr(
        provider.client.embeddings,
        "create",
        create_mock,
    )

    result = await provider.embed("Política de devoluciones")

    assert result == expected_embedding

    create_mock.assert_awaited_once_with(
        model="text-embedding-3-small",
        input="Política de devoluciones",
    )
