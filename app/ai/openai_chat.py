from openai import AsyncOpenAI

from app.core.config import settings
from app.exceptions.ai import AIConfigurationError


class OpenAIChatProvider:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise AIConfigurationError("AI provider credentials are not configured")

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
        )

        self.model = settings.openai_chat_model

    async def generate(
        self,
        *,
        question: str,
        context: str,
    ) -> str:
        response = await self.client.responses.create(
            model=self.model,
            instructions=(
                "Responde siempre en español. "
                "Responde la pregunta del usuario utilizando únicamente "
                "la información proporcionada en el contexto. "
                "No inventes información ni utilices conocimiento externo. "
                "Si el contexto no contiene información suficiente para "
                "responder, indica claramente que no tienes información "
                "suficiente para responder la pregunta."
            ),
            input=(f"Context:\n{context}\n\nQuestion:\n{question}"),
        )

        return response.output_text
