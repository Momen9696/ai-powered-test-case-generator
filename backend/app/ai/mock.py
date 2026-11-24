"""Deterministic local provider.

Results come from the rules in services.generator. The same source and analysis
always produce the same cases. Nothing here is a language-model response.
"""

from __future__ import annotations

import json
import time

from app.ai.base import AIProvider, GenerationRequest, ProviderResult, TokenUsage
from app.schemas import GeneratedCase
from app.services.generator import build_cases


class MockProvider(AIProvider):
    name = "mock"
    model = "deterministic-rules-v1"

    def generate(self, request: GenerationRequest) -> ProviderResult:
        started = time.perf_counter()
        drafted = build_cases(request.source_text, request.analysis, request.selected_types)
        cases = [GeneratedCase.model_validate(item).model_dump() for item in drafted]
        raw = json.dumps({"test_cases": cases}, ensure_ascii=False)
        usage = TokenUsage(
            prompt_tokens=max(1, len(request.source_text) // 4),
            completion_tokens=max(1, len(raw) // 4),
            source="estimated",
            note=(
                "Estimated by dividing character counts by 4. "
                "The mock provider did not call an external model and these are not billed tokens."
            ),
        )
        return ProviderResult(
            cases=cases,
            raw_text=raw,
            model=self.model,
            deterministic=True,
            latency_ms=max(0, int((time.perf_counter() - started) * 1000)),
            token_usage=usage,
            recovered=request.mode == "repair",
        )
