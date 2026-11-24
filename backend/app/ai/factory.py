"""Select a provider from saved settings and environment secrets."""

from __future__ import annotations

from app.ai.base import AIProvider
from app.ai.mock import MockProvider
from app.ai.remote import AnthropicProvider, OpenAIProvider
from app.config import Settings
from app.schemas import ProviderConfigError


def build_provider(settings: Settings, provider_name: str, model: str) -> AIProvider:
    name = (provider_name or "mock").strip().lower()
    if name == "mock":
        return MockProvider()
    if name == "openai":
        return OpenAIProvider(settings, model)
    if name == "anthropic":
        return AnthropicProvider(settings, model)
    raise ProviderConfigError(f"Unknown provider '{provider_name}'. Use mock, openai, or anthropic.")
