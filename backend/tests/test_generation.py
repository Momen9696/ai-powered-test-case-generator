from app.examples import SAMPLE_TRANSFER_STORY
from app.services.analysis import analyze_requirements
from app.services.generator import build_cases
from app.services.quality import coverage_report, find_duplicate_groups


def test_mock_cases_are_deterministic_and_typed():
    analysis = analyze_requirements(SAMPLE_TRANSFER_STORY)
    first = build_cases(SAMPLE_TRANSFER_STORY, analysis)
    second = build_cases(SAMPLE_TRANSFER_STORY, analysis)
    assert [case["title"] for case in first] == [case["title"] for case in second]
    types = {case["test_type"] for case in first}
    assert {
        "functional",
        "positive",
        "negative",
        "boundary",
        "edge",
        "error_handling",
        "security",
        "api",
        "ui",
    } <= types
    security = next(case for case in first if case["test_type"] == "security")
    assert security["scenario_origin"] == "inferred"
    outside = next(case for case in first if "outside the stated boundary" in case["title"])
    assert outside["scenario_origin"] == "inferred"
    stated = next(case for case in first if case["title"].startswith("Boundary values stated"))
    assert stated["scenario_origin"] == "extracted"
    assert "score" not in first[0]


def test_selected_types_limit_output():
    analysis = analyze_requirements(SAMPLE_TRANSFER_STORY)
    cases = build_cases(SAMPLE_TRANSFER_STORY, analysis, ["positive"])
    assert cases
    assert {case["test_type"] for case in cases} == {"positive"}


def test_missing_criteria_still_produce_a_case():
    text = "Something vague about reports."
    analysis = analyze_requirements(text)
    cases = build_cases(text, analysis, ["functional"])
    assert cases[0]["requirement_ref"] == "REQ-UNSPECIFIED"
    assert cases[0]["scenario_origin"] == "inferred"


def test_duplicate_detection_groups_similar_titles():
    cases = [
        {"id": "1", "case_key": "TC-0001", "title": "Verify transfer between customer accounts"},
        {"id": "2", "case_key": "TC-0002", "title": "Verify transfer between customer accounts now"},
        {"id": "3", "case_key": "TC-0003", "title": "Reset the forgotten password email template"},
    ]
    groups = find_duplicate_groups(cases, threshold=0.6)
    assert len(groups) == 1
    keys = {item["case_key"] for item in groups[0]["cases"]}
    assert keys == {"TC-0001", "TC-0002"}


def test_coverage_maps_requirement_references():
    analysis = {
        "acceptance_criteria": [
            {"id": "AC-1", "statement": "One", "origin": "extracted"},
            {"id": "AC-2", "statement": "Two", "origin": "extracted"},
        ]
    }
    cases = [
        {"id": "c1", "case_key": "TC-0001", "title": "A", "requirement_ref": "AC-1", "test_type": "functional"}
    ]
    report = coverage_report(analysis, cases)
    assert report["coverage_percent"] == 50.0
    assert report["uncovered"][0]["id"] == "AC-2"
    assert report["llm_used"] is False
