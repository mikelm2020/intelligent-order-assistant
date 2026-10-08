"""Offline demonstration providers; these are not semantic embeddings or an LLM."""

import re


class DemoEmbeddingProvider:
    async def embed(self, text: str) -> list[float]:
        topics = (
            r"\b(?:devoluciones|devolver|devolución)\b",
            r"\b(?:envío|envíos|entrega|entregas)\b",
            r"\b(?:pago|pagos|tarjeta|transferencia)\b",
        )
        vector = [0.0] * 1536
        matched = False
        for index, pattern in enumerate(topics):
            if re.search(pattern, text.lower()):
                vector[index] = 1.0
                matched = True
        if not matched:
            vector[3] = 1.0
        return vector


class DemoChatProvider:
    async def generate(self, *, question: str, context: str) -> str:
        return f"Documentación recuperada (modo demo):\n{context}"
