from app.ai.chat import ChatProvider
from app.ai.demo import DemoChatProvider
from app.ai.openai_chat import OpenAIChatProvider
from app.core.config import settings


def get_chat_provider() -> ChatProvider:
    if settings.ai_provider == "demo":
        return DemoChatProvider()
    return OpenAIChatProvider()
