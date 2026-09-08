from typing import Protocol


class ChatProvider(Protocol):
    async def generate(
        self,
        *,
        question: str,
        context: str,
    ) -> str:
        """Generate an answer using the supplied context."""
        ...
