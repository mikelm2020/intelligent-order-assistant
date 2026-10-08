import pytest

from app.ai.demo import DemoChatProvider, DemoEmbeddingProvider


@pytest.mark.asyncio
async def test_demo_vectors_have_required_dimensions_and_separate_topics():
    provider = DemoEmbeddingProvider()
    returns = await provider.embed("¿Puedo devolver un producto?")
    assert len(returns) == 1536
    assert returns == await provider.embed("Política de devoluciones")
    assert returns != await provider.embed("Información de pagos")


@pytest.mark.asyncio
async def test_demo_chat_only_echoes_context():
    answer = await DemoChatProvider().generate(
        question="inventar", context="Contenido documentado"
    )
    assert answer == "Documentación recuperada (modo demo):\nContenido documentado"
