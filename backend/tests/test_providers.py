import json

import httpx

from app.ai.base import GenerationRequest, ProviderResult, TokenUsage
from app.ai.factory import build_provider
from app.ai.mock import MockProvider
from app.ai.remote import OpenAIProvider
from app.ai.validation import parse_test_cases
from app.config import Settings
from app.examples import SAMPLE_TRANSFER_STORY
from app.schemas import AIOutputError, ProviderConfigError
from app.services.analysis import analyze_requirements
from app.services.workflow import obtain_cases


VALID_CASE = {
    "title": "Accept a valid transfer",
    "description": "Happy path",
    "requirement_ref": "AC-1",
    "preconditions": ["Customer is signed in"],
    "steps": ["Submit a transfer of 10 USD"],
    "test_data": {"amount": "10"},
    "expected_result": "The transfer is accepted.",
    "test_type": "positive",
    "priority": "high",
    "risk_level": "medium",
    "automation_suitability": "high",
    "tags": ["positive"],
    "scenario_origin": "extracted",
}


def _request() -> GenerationRequest:
    return GenerationRequest(
        source_text=SAMPLE_TRANSFER_STORY,
        analysis=analyze_requirements(SAMPLE_TRANSFER_STORY),
        selected_types=["functional"],
    )


def test_mock_provider_reports_estimates_not_provider_usage():
    result = MockProvider().generate(_request())
    assert result.deterministic is True
    assert result.model == "deterministic-rules-v1"
    assert result.token_usage.source == "estimated"
    assert "not billed" in result.token_usage.note
    assert result.cases


def test_parse_accepts_markdown_fence():
    raw = "```json\n" + json.dumps({"test_cases": [VALID_CASE]}) + "\n```"
    cases = parse_test_cases(raw)
    assert cases[0].title == VALID_CASE["title"]


def test_parse_rejects_invalid_json():
    try:
        parse_test_cases("this is not json")
    except AIOutputError as exc:
        assert "not valid JSON" in exc.message
    else:
        raise AssertionError("expected AIOutputError")


class ScriptedProvider:
    name = "scripted"
    model = "scripted-test"

    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)

    def generate(self, request: GenerationRequest) -> ProviderResult:
        raw = self.outputs.pop(0)
        cases = []
        try:
            cases = [item.model_dump() for item in parse_test_cases(raw)]
        except AIOutputError:
            cases = []
        return ProviderResult(
            cases=cases,
            raw_text=raw,
            model=self.model,
            deterministic=False,
            latency_ms=1,
            token_usage=TokenUsage(
                prompt_tokens=1,
                completion_tokens=1,
                source="provider",
                note="Fixture usage for a scripted provider.",
            ),
            recovered=request.mode == "repair",
        )


def test_invalid_output_is_repaired_once():
    good = json.dumps({"test_cases": [VALID_CASE]})
    cases, result, recovered = obtain_cases(ScriptedProvider(["not-json", good]), _request())
    assert recovered is True
    assert cases[0].requirement_ref == "AC-1"
    assert result.model == "scripted-test"


def test_invalid_output_fails_when_repair_also_fails():
    try:
        obtain_cases(ScriptedProvider(["not-json", "still-not-json"]), _request())
    except AIOutputError as exc:
        assert "repair" in exc.message
    else:
        raise AssertionError("expected AIOutputError")


def test_openai_requires_a_key():
    try:
        build_provider(Settings(openai_api_key=""), "openai", "")
    except ProviderConfigError as exc:
        assert "OPENAI_API_KEY" in exc.message
    else:
        raise AssertionError("expected ProviderConfigError")


def test_openai_adapter_reads_usage_and_hides_the_key(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "choices": [{"message": {"content": json.dumps({"test_cases": [VALID_CASE]})}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 7},
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    settings = Settings(openai_api_key="sk-local-test-value", openai_model="gpt-test")
    provider = OpenAIProvider(settings, "")
    result = provider.generate(_request())
    assert result.token_usage.source == "provider"
    assert result.token_usage.prompt_tokens == 11
    assert result.cases[0]["title"] == VALID_CASE["title"]
    assert captured["headers"]["Authorization"] == "Bearer sk-local-test-value"
    assert "sk-local-test-value" not in json.dumps(result.model_dump())
    assert result.deterministic is False


def test_openai_http_error_has_no_body(monkeypatch):
    class FakeResponse:
        status_code = 401

        def json(self):
            return {"error": {"message": "bad key sk-secret-should-not-leak"}}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers=None, json=None):
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    provider = OpenAIProvider(Settings(openai_api_key="sk-local-test-value"), "")
    try:
        provider.generate(_request())
    except Exception as exc:
        text = str(exc)
        assert "401" in text
        assert "sk-secret" not in text
    else:
        raise AssertionError("expected provider error")
