class FakeEmbeddingProvider:
    async def embed(self, text: str) -> list[float]:
        value = float(len(text))
        return [value] + [0.0] * 1535
