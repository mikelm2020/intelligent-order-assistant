from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.assistant import get_assistant_chat_provider as get_chat_provider
from app.api.v1.assistant import (
    get_assistant_embedding_provider as get_embedding_provider,
)
from app.main import app
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


@pytest.fixture
def mock_embedding_provider():
    provider = AsyncMock()
    provider.embed.return_value = [1.0, 0.0, 0.0] + [0.0] * 1533

    app.dependency_overrides[get_embedding_provider] = lambda: provider

    yield provider

    app.dependency_overrides.pop(get_embedding_provider, None)


@pytest.fixture
def mock_chat_provider():
    provider = AsyncMock()
    provider.generate.return_value = (
        "Puedes devolver el producto dentro de 30 días si conserva su empaque original."
    )

    app.dependency_overrides[get_chat_provider] = lambda: provider

    yield provider

    app.dependency_overrides.pop(get_chat_provider, None)


@pytest.mark.asyncio
async def test_assistant_returns_rag_answer(
    client,
    session: AsyncSession,
    mock_embedding_provider,
    mock_chat_provider,
):
    document = Document(
        title="Política de devoluciones",
        content="Documento de prueba",
        source="test",
    )

    session.add(document)
    await session.flush()

    session.add(
        DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content=(
                "Las devoluciones se aceptan dentro de 30 días "
                "si el producto conserva su empaque original."
            ),
            embedding=[1.0, 0.0, 0.0] + [0.0] * 1533,
        )
    )

    await session.commit()

    response = await client.post(
        "/api/v1/assistant/ask",
        json={
            "question": "¿Puedo devolver un producto después de 20 días?",
            "limit": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == (
        "Puedes devolver el producto dentro de 30 días si conserva su empaque original."
    )

    mock_embedding_provider.embed.assert_awaited_once_with(
        "¿Puedo devolver un producto después de 20 días?"
    )

    mock_chat_provider.generate.assert_awaited_once_with(
        question="¿Puedo devolver un producto después de 20 días?",
        context=(
            "Las devoluciones se aceptan dentro de 30 días "
            "si el producto conserva su empaque original."
        ),
    )


@pytest.mark.asyncio
async def test_assistant_returns_fallback_when_no_relevant_context(
    client,
    session: AsyncSession,
    mock_embedding_provider,
    mock_chat_provider,
):
    document = Document(
        title="Política de devoluciones",
        content="Documento de prueba",
        source="test",
    )

    session.add(document)
    await session.flush()

    session.add(
        DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="Información no relacionada con la pregunta.",
            embedding=[0.0, 1.0, 0.0] + [0.0] * 1533,
        )
    )

    await session.commit()

    response = await client.post(
        "/api/v1/assistant/ask",
        json={
            "question": "¿Ofrecen garantía de cinco años?",
            "limit": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == (
        "No tengo información suficiente en la documentación "
        "disponible para responder esa pregunta."
    )

    mock_embedding_provider.embed.assert_awaited_once_with(
        "¿Ofrecen garantía de cinco años?"
    )

    mock_chat_provider.generate.assert_not_awaited()
