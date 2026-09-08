from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.openai_chat import OpenAIChatProvider


@pytest.mark.asyncio
async def test_generate_returns_response_text(monkeypatch):
    provider = OpenAIChatProvider()

    response = MagicMock()
    response.output_text = "Las devoluciones se aceptan dentro de 30 días."

    create_mock = AsyncMock(return_value=response)

    monkeypatch.setattr(
        provider.client.responses,
        "create",
        create_mock,
    )

    result = await provider.generate(
        question="¿Cuál es la política de devoluciones?",
        context=("Las devoluciones se aceptan dentro de 30 días."),
    )

    assert result == ("Las devoluciones se aceptan dentro de 30 días.")

    create_mock.assert_awaited_once_with(
        model="gpt-5.6-luna",
        instructions=(
            "Responde siempre en español. "
            "Responde la pregunta del usuario utilizando únicamente "
            "la información proporcionada en el contexto. "
            "No inventes información ni utilices conocimiento externo. "
            "Si el contexto no contiene información suficiente para "
            "responder, indica claramente que no tienes información "
            "suficiente para responder la pregunta."
        ),
        input=(
            "Context:\n"
            "Las devoluciones se aceptan dentro de 30 días.\n\n"
            "Question:\n"
            "¿Cuál es la política de devoluciones?"
        ),
    )
