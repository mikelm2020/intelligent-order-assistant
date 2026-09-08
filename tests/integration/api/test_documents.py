from unittest.mock import AsyncMock

import pytest

from app.ai.factory import get_embedding_provider
from app.main import app


@pytest.fixture
def mock_embedding_provider():
    provider = AsyncMock()

    provider.embed.return_value = [1.0] + [0.0] * 1535

    app.dependency_overrides[get_embedding_provider] = lambda: provider

    yield provider

    app.dependency_overrides.pop(get_embedding_provider, None)


@pytest.mark.asyncio
async def test_create_document(
    client,
    mock_embedding_provider,
):
    response = await client.post(
        "/api/v1/documents",
        json={
            "title": "Política de devoluciones",
            "content": "Las devoluciones se aceptan dentro de 30 días.",
            "source": "test",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["title"] == "Política de devoluciones"
    assert data["source"] == "test"
    assert data["content"] == ("Las devoluciones se aceptan dentro de 30 días.")

    mock_embedding_provider.embed.assert_awaited_once()
