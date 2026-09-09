from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.rag import RAGService


@pytest.mark.asyncio
async def test_answer_builds_context_and_generates_response():
    retrieval_service = AsyncMock()
    chat_provider = AsyncMock()

    chunk_1 = MagicMock()
    chunk_1.content = "Las devoluciones se aceptan dentro de 30 días."

    chunk_2 = MagicMock()
    chunk_2.content = "El producto debe conservar su empaque original."

    retrieval_service.search.return_value = [
        chunk_1,
        chunk_2,
    ]

    chat_provider.generate.return_value = (
        "Puedes devolver el producto dentro de 30 días si conserva su empaque original."
    )

    service = RAGService(
        retrieval_service=retrieval_service,
        chat_provider=chat_provider,
    )

    result = await service.answer(
        "¿Cuál es la política de devoluciones?",
        limit=2,
    )

    assert result == (
        "Puedes devolver el producto dentro de 30 días si conserva su empaque original."
    )

    retrieval_service.search.assert_awaited_once_with(
        "¿Cuál es la política de devoluciones?",
        limit=2,
        max_distance=None,
    )

    chat_provider.generate.assert_awaited_once_with(
        question="¿Cuál es la política de devoluciones?",
        context=(
            "Las devoluciones se aceptan dentro de 30 días.\n\n"
            "El producto debe conservar su empaque original."
        ),
    )


@pytest.mark.asyncio
async def test_answer_rejects_empty_question():
    retrieval_service = AsyncMock()
    chat_provider = AsyncMock()

    service = RAGService(
        retrieval_service=retrieval_service,
        chat_provider=chat_provider,
    )

    with pytest.raises(
        ValueError,
        match="question cannot be empty",
    ):
        await service.answer("   ")

    retrieval_service.search.assert_not_awaited()
    chat_provider.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_answer_passes_max_distance_to_retrieval():
    retrieval_service = AsyncMock()
    chat_provider = AsyncMock()

    retrieval_service.search.return_value = []
    chat_provider.generate.return_value = (
        "No tengo información suficiente para responder."
    )

    service = RAGService(
        retrieval_service=retrieval_service,
        chat_provider=chat_provider,
    )

    await service.answer(
        "¿Ofrecen garantía de cinco años?",
        limit=3,
        max_distance=0.4,
    )

    retrieval_service.search.assert_awaited_once_with(
        "¿Ofrecen garantía de cinco años?",
        limit=3,
        max_distance=0.4,
    )


@pytest.mark.asyncio
async def test_answer_returns_fallback_when_no_relevant_chunks():
    retrieval_service = AsyncMock()
    chat_provider = AsyncMock()

    retrieval_service.search.return_value = []

    service = RAGService(
        retrieval_service=retrieval_service,
        chat_provider=chat_provider,
    )

    result = await service.answer(
        "¿La empresa ofrece garantía de cinco años?",
        limit=5,
        max_distance=0.4,
    )

    assert result == (
        "No tengo información suficiente en la documentación "
        "disponible para responder esa pregunta."
    )

    retrieval_service.search.assert_awaited_once_with(
        "¿La empresa ofrece garantía de cinco años?",
        limit=5,
        max_distance=0.4,
    )

    chat_provider.generate.assert_not_awaited()
