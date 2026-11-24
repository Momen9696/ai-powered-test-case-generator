"""Shared provider types and prompt text.

Prompt templates are used by remote adapters. The mock provider does not call a model.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas import ALL_TEST_TYPES

PROMPT_VERSION = "1.0.0"

SYSTEM_PROMPT = """You are a senior QA analyst. Return JSON only.
The JSON object must be {"test_cases": [ ... ]}.
Each test case needs these fields:
title, description, requirement_ref, preconditions (array of strings),
steps (array of strings), test_data (object whose values are strings),
expected_result, test_type, priority, risk_level, automation_suitability,
tags (array of strings), scenario_origin ("extracted" or "inferred").
test_type must be one of: functional, positive, negative, boundary, edge, error_handling, security, api, ui.
priority and risk_level must be one of: critical, high, medium, low.
automation_suitability must be one of: high, medium, low, manual_only.
Use scenario_origin "extracted" only when the source text states that scenario.
Use "inferred" for suggestions, gaps, and standard techniques such as values outside a stated range.
Do not wrap the JSON in markdown.
Do not include a quality score.
"""


class GenerationRequest(BaseModel):
    source_text: str
    analysis: dict
    selected_types: list[str] = Field(default_factory=lambda: list(ALL_TEST_TYPES))
    mode: Literal["generate", "repair"] = "generate"
    repair_raw: str = ""
    temperature: float = 0.2
    max_tokens: int = 4000


class TokenUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    source: Literal["provider", "estimated"]
    note: str


class ProviderResult(BaseModel):
    cases: list[dict] = Field(default_factory=list)
    raw_text: str = ""
    model: str
    deterministic: bool
    latency_ms: int
    token_usage: TokenUsage
    recovered: bool = False


class AIProvider:
    name = "base"

    def generate(self, request: GenerationRequest) -> ProviderResult:
        raise NotImplementedError


def user_prompt(request: GenerationRequest) -> str:
    return json.dumps(
        {
            "task": "Generate reviewable test cases for the requested types only.",
            "requested_types": request.selected_types,
            "source": request.source_text,
            "analysis": request.analysis,
        },
        ensure_ascii=False,
    )


def repair_prompt(raw: str) -> str:
    clipped = raw[:8000]
    return (
        "The previous response was not valid JSON for the test case schema. "
        "Return a corrected JSON object only, with a test_cases array.\n\n"
        f"{clipped}"
    )
