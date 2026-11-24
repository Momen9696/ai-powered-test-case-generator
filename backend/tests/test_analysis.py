from app.examples import SAMPLE_AMBIGUOUS_STORY, SAMPLE_REQUIREMENTS_DOC, SAMPLE_TRANSFER_STORY
from app.services.analysis import analyze_requirements


def test_transfer_story_extracts_facts():
    payload = analyze_requirements(SAMPLE_TRANSFER_STORY, "user_story")
    actors = [item["statement"].lower() for item in payload["actors"]]
    assert "customer" in actors
    assert all(item["origin"] == "extracted" for item in payload["actors"])
    assert len(payload["acceptance_criteria"]) == 4
    assert payload["acceptance_criteria"][0]["evidence"]
    statements = " ".join(item["statement"] for item in payload["constraints"])
    assert "0.01" in statements
    assert "10000" in statements
    assert "25000" in statements
    assert payload["summary"]["llm_used"] is False


def test_analysis_is_deterministic():
    first = analyze_requirements(SAMPLE_TRANSFER_STORY)
    second = analyze_requirements(SAMPLE_TRANSFER_STORY)
    assert first == second


def test_ambiguous_terms_quote_the_source():
    payload = analyze_requirements(SAMPLE_AMBIGUOUS_STORY)
    evidences = " ".join((item.get("evidence") or "") for item in payload["ambiguities"]).lower()
    assert "fast" in evidences
    assert "user-friendly" in evidences or "intuitive" in evidences
    assert "tbd" in evidences
    assert any(item["origin"] == "extracted" for item in payload["ambiguities"])


def test_missing_acceptance_criteria_are_inferred():
    payload = analyze_requirements("The customer wants a report of recent activity.")
    missing = " ".join(item["statement"] for item in payload["missing_information"])
    assert "No acceptance criteria" in missing
    assert all(item["origin"] == "inferred" for item in payload["missing_information"])
    assert all(item["evidence"] is None for item in payload["missing_information"])


def test_malformed_text_does_not_fail():
    payload = analyze_requirements("@@@ ### $$$ ???")
    assert payload["summary"]["detector"] == "heuristic-v1"
    assert payload["acceptance_criteria"] == []
    assert payload["missing_information"]


def test_requirements_document_finds_rules_and_dependency():
    payload = analyze_requirements(SAMPLE_REQUIREMENTS_DOC, "requirements_document")
    actor_names = {item["statement"].lower() for item in payload["actors"]}
    assert "clerk" in actor_names
    assert "manager" in actor_names
    assert payload["business_rules"]
    assert payload["dependencies"]
    assert payload["acceptance_criteria"]
    assert any(item["origin"] == "extracted" for item in payload["dependencies"])
