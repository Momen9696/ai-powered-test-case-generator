"""Parse and validate structured provider output."""

from __future__ import annotations

import json
import re

from app.schemas import AIOutputError, GeneratedCase


def _strip_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_test_cases(raw: str) -> list[GeneratedCase]:
    if not raw or not raw.strip():
        raise AIOutputError("Provider returned an empty response")
    text = _strip_fence(raw)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIOutputError("Provider response was not valid JSON") from exc
    if isinstance(data, dict) and "test_cases" in data:
        data = data["test_cases"]
    if not isinstance(data, list):
        raise AIOutputError("Provider JSON did not contain a test_cases list")
    cases: list[GeneratedCase] = []
    errors: list[str] = []
    for index, item in enumerate(data, start=1):
        try:
            cases.append(GeneratedCase.model_validate(item))
        except Exception as exc:  # pydantic ValidationError
            errors.append(f"case {index}: {exc}")
    if errors:
        raise AIOutputError("Provider JSON failed schema validation: " + "; ".join(errors[:3]))
    if not cases:
        raise AIOutputError("Provider returned no test cases")
    return cases


def coerce_result(cases: list[dict], raw_text: str) -> list[GeneratedCase]:
    if cases:
        return parse_test_cases(json.dumps({"test_cases": cases}))
    return parse_test_cases(raw_text)
