"""Remote provider adapters.

These classes call a configured HTTP API. Tests stub the HTTP client.
The application starts in mock mode and does not require either key.
"""

from __future__ import annotations

import time

import httpx

from app.ai.base import (
    SYSTEM_PROMPT,
    AIProvider,
    GenerationRequest,
    ProviderResult,
    TokenUsage,
    repair_prompt,
    user_prompt,
)
from app.ai.validation import parse_test_cases
from app.config import Settings
from app.schemas import ProviderConfigError, ProviderRequestError


class _RemoteProvider(AIProvider):
    def __init__(self, settings: Settings, model: str) -> None:
        self.settings = settings
        self.model_name = model

    def _message(self, request: GenerationRequest) -> str:
        if request.mode == "repair":
            return repair_prompt(request.repair_raw)
        return user_prompt(request)

    def generate(self, request: GenerationRequest) -> ProviderResult:
        started = time.perf_counter()
        raw, usage = self._complete(self._message(request), request)
        latency_ms = int((time.perf_counter() - started) * 1000)
        # Parse here so a schema failure surfaces before the caller treats it as success.
        # The service still performs one repair attempt when this raises.
        cases = []
        try:
            cases = [item.model_dump() for item in parse_test_cases(raw)]
        except Exception:
            cases = []
        return ProviderResult(
            cases=cases,
            raw_text=raw,
            model=self.model_name,
            deterministic=False,
            latency_ms=latency_ms,
            token_usage=usage,
        )

    def _complete(self, prompt: str, request: GenerationRequest) -> tuple[str, TokenUsage]:
        raise NotImplementedError


class OpenAIProvider(_RemoteProvider):
    name = "openai"

    def __init__(self, settings: Settings, model: str) -> None:
        if not settings.openai_api_key:
            raise ProviderConfigError(
                "OpenAI is selected but OPENAI_API_KEY is not set on the server."
            )
        super().__init__(settings, model or settings.openai_model)

    def _complete(self, prompt: str, request: GenerationRequest) -> tuple[str, TokenUsage]:
        url = self.settings.openai_base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model_name,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise ProviderRequestError("The OpenAI request failed before a response was received.") from exc
        if response.status_code >= 400:
            raise ProviderRequestError(f"OpenAI returned HTTP {response.status_code}.")
        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except Exception as exc:
            raise ProviderRequestError("OpenAI returned a response without message content.") from exc
        usage_body = body.get("usage") or {}
        usage = TokenUsage(
            prompt_tokens=usage_body.get("prompt_tokens"),
            completion_tokens=usage_body.get("completion_tokens"),
            source="provider",
            note="Token counts were reported by the provider response.",
        )
        return str(content), usage


class AnthropicProvider(_RemoteProvider):
    name = "anthropic"

    def __init__(self, settings: Settings, model: str) -> None:
        if not settings.anthropic_api_key:
            raise ProviderConfigError(
                "Anthropic is selected but ANTHROPIC_API_KEY is not set on the server."
            )
        super().__init__(settings, model or settings.anthropic_model)

    def _complete(self, prompt: str, request: GenerationRequest) -> tuple[str, TokenUsage]:
        url = self.settings.anthropic_base_url.rstrip("/") + "/v1/messages"
        payload = {
            "model": self.model_name,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(
                "The Anthropic request failed before a response was received."
            ) from exc
        if response.status_code >= 400:
            raise ProviderRequestError(f"Anthropic returned HTTP {response.status_code}.")
        try:
            body = response.json()
            content = body["content"][0]["text"]
        except Exception as exc:
            raise ProviderRequestError("Anthropic returned a response without text content.") from exc
        usage_body = body.get("usage") or {}
        usage = TokenUsage(
            prompt_tokens=usage_body.get("input_tokens"),
            completion_tokens=usage_body.get("output_tokens"),
            source="provider",
            note="Token counts were reported by the provider response.",
        )
        return str(content), usage

