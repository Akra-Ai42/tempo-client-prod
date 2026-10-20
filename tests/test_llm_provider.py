"""Tests pour l'interface LLMProvider."""

from app.llm.base import LLMProvider, LLMResponse
from app.llm.adapters import OpenRouterProvider, get_llm_provider


def test_factory_returns_openrouter():
    """Par défaut, la factory retourne un OpenRouterProvider."""
    provider = get_llm_provider()
    assert isinstance(provider, OpenRouterProvider)
    assert provider.provider_name == "openrouter"


def test_llm_response_dataclass():
    """La dataclass LLMResponse accepte tous les champs attendus."""
    r = LLMResponse(
        text="hello",
        model="llama-3.3-70b",
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        cost_usd=0.0001,
    )
    assert r.text == "hello"
    assert r.cost_usd == 0.0001


def test_provider_is_abstract():
    """LLMProvider ne peut pas être instancié directement."""
    import pytest
    with pytest.raises(TypeError):
        LLMProvider()
