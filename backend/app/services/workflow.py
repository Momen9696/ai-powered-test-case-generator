"""Generation workflow: validate provider output, recover once, then store."""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.base import PROMPT_VERSION, AIProvider, GenerationRequest
from app.ai.validation import coerce_result
from app.models import AnalysisRecord, GenerationRun, TestCaseRecord, TestSuite, utcnow
from app.schemas import AIOutputError, GeneratedCase
from app.services.analysis import analyze_requirements
from app.services.quality import flag_duplicates


def obtain_cases(provider: AIProvider, request: GenerationRequest) -> tuple[list[GeneratedCase], object, bool]:
    result = provider.generate(request)
    try:
        return coerce_result(result.cases, result.raw_text), result, bool(result.recovered)
    except AIOutputError:
        if request.mode == "repair":
            raise AIOutputError("Provider output remained invalid after one repair attempt")
        repair = request.model_copy(update={"mode": "repair", "repair_raw": result.raw_text or ""})
        second = provider.generate(repair)
        try:
            cases = coerce_result(second.cases, second.raw_text)
        except AIOutputError as exc:
            raise AIOutputError("Provider output remained invalid after one repair attempt") from exc
        return cases, second, True


def store_analysis(db: Session, project_id: str, source_id: str, content: str, kind: str) -> AnalysisRecord:
    payload = analyze_requirements(content, kind)
    row = AnalysisRecord(project_id=project_id, source_id=source_id, payload=payload)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _next_number(db: Session, project_id: str) -> int:
    keys = db.scalars(select(TestCaseRecord.case_key).where(TestCaseRecord.project_id == project_id)).all()
    numbers = []
    for key in keys:
        match = re.fullmatch(r"TC-(\d+)", key or "")
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers, default=0) + 1


def store_generation(
    db: Session,
    *,
    project_id: str,
    source_id: str,
    analysis: AnalysisRecord,
    selected_types: list[str],
    suite_name: str | None,
    provider: AIProvider,
    temperature: float,
    max_tokens: int,
) -> tuple[GenerationRun, list[TestCaseRecord], TestSuite | None]:
    request = GenerationRequest(
        source_text=_source_text(db, source_id),
        analysis=analysis.payload,
        selected_types=selected_types,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    parameters = {
        "types": selected_types,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "temperature_applied": provider.name != "mock",
        "prompt_version": PROMPT_VERSION,
        "analysis_id": analysis.id,
    }
    try:
        cases, result, recovered = obtain_cases(provider, request)
    except AIOutputError as exc:
        run = GenerationRun(
            project_id=project_id,
            source_id=source_id,
            provider=provider.name,
            model=getattr(provider, "model", "") or getattr(provider, "model_name", ""),
            status="failed",
            parameters=parameters,
            stats={"recovered": False},
            error=exc.message,
        )
        db.add(run)
        db.commit()
        raise

    dumped = flag_duplicates([case.model_dump() for case in cases])
    suite = None
    if suite_name:
        suite = TestSuite(project_id=project_id, name=suite_name, description="Created with a generation run.")
        db.add(suite)
        db.flush()

    number = _next_number(db, project_id)
    records: list[TestCaseRecord] = []
    for offset, case in enumerate(dumped):
        metadata = {
            "provider": provider.name,
            "model": result.model,
            "prompt_version": PROMPT_VERSION,
            "latency_ms": result.latency_ms,
            "token_usage": result.token_usage.model_dump(),
            "deterministic": result.deterministic,
            "scenario_origin": case["scenario_origin"],
            "recovered_from_invalid_output": recovered,
            "produced_by_external_model": not result.deterministic,
            "possible_duplicate_of": case.get("possible_duplicate_of"),
            "temperature_applied": provider.name != "mock",
        }
        # The mock path must not look like a scored model evaluation.
        metadata.pop("score", None)
        record = TestCaseRecord(
            project_id=project_id,
            suite_id=suite.id if suite else None,
            source_id=source_id,
            case_key=f"TC-{number + offset:04d}",
            title=case["title"],
            description=case["description"],
            requirement_ref=case["requirement_ref"],
            preconditions=case["preconditions"],
            steps=case["steps"],
            test_data=case["test_data"],
            expected_result=case["expected_result"],
            test_type=case["test_type"],
            priority=case["priority"],
            risk_level=case["risk_level"],
            automation_suitability=case["automation_suitability"],
            tags=case["tags"],
            generation_metadata=metadata,
            status="draft",
        )
        db.add(record)
        records.append(record)

    by_type: dict[str, int] = {}
    for record in records:
        by_type[record.test_type] = by_type.get(record.test_type, 0) + 1
    run = GenerationRun(
        project_id=project_id,
        source_id=source_id,
        provider=provider.name,
        model=result.model,
        status="completed",
        parameters=parameters,
        stats={
            "case_count": len(records),
            "by_type": by_type,
            "recovered_from_invalid_output": recovered,
            "duplicate_flags": sum(1 for case in dumped if case.get("possible_duplicate_of")),
            "deterministic": result.deterministic,
            "latency_ms": result.latency_ms,
            "token_usage": result.token_usage.model_dump(),
        },
        error=None,
    )
    db.add(run)
    db.commit()
    for record in records:
        db.refresh(record)
    db.refresh(run)
    return run, records, suite


def _source_text(db: Session, source_id: str) -> str:
    from app.models import RequirementSource

    source = db.get(RequirementSource, source_id)
    if source is None:
        return ""
    return source.content


def touch_project(db: Session, project) -> None:
    project.updated_at = utcnow()
    db.add(project)
