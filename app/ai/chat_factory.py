from app.ai.chat import ChatProvider
from app.ai.openai_chat import OpenAIChatProvider


def get_chat_provider() -> ChatProvider:
    return OpenAIChatProvider()
