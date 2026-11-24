"""Excel, CSV, and JSON exports."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from io import BytesIO

import pandas as pd

ABOUT_NOTE = (
    "The Provider and Deterministic columns describe how each row was produced. "
    "Rows from the mock provider were created by local deterministic rules. "
    "They were not returned by an external language model, and this file contains no model quality score."
)


def _join(items: object) -> str:
    if isinstance(items, list):
        return "\n".join(f"{index}. {value}" for index, value in enumerate(items, start=1))
    return "" if items is None else str(items)


def _rows(cases: list[dict]) -> list[dict]:
    rows = []
    for case in cases:
        metadata = case.get("generation_metadata") or {}
        usage = metadata.get("token_usage") or {}
        rows.append(
            {
                "Case Key": case.get("case_key") or "",
                "Title": case.get("title") or "",
                "Description": case.get("description") or "",
                "Requirement Reference": case.get("requirement_ref") or "",
                "Preconditions": _join(case.get("preconditions")),
                "Test Steps": _join(case.get("steps")),
                "Test Data": json.dumps(case.get("test_data") or {}, ensure_ascii=False),
                "Expected Result": case.get("expected_result") or "",
                "Test Type": case.get("test_type") or "",
                "Priority": case.get("priority") or "",
                "Risk Level": case.get("risk_level") or "",
                "Automation Suitability": case.get("automation_suitability") or "",
                "Tags": ", ".join(case.get("tags") or []),
                "Status": case.get("status") or "",
                "Scenario Origin": metadata.get("scenario_origin") or "",
                "Provider": metadata.get("provider") or "",
                "Model": metadata.get("model") or "",
                "Deterministic": metadata.get("deterministic"),
                "Token Usage Source": usage.get("source") or "",
            }
        )
    return rows


def _filename(project_name: str, extension: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", project_name).strip("-").lower() or "project"
    return f"{slug}-test-cases.{extension}"


def export_cases(project_name: str, project_id: str, is_demo: bool, cases: list[dict], fmt: str) -> tuple[bytes, str, str]:
    rows = _rows(cases)
    if fmt == "csv":
        frame = pd.DataFrame(rows)
        data = frame.to_csv(index=False).encode("utf-8")
        return data, "text/csv; charset=utf-8", _filename(project_name, "csv")
    if fmt == "xlsx":
        frame = pd.DataFrame(rows)
        about = pd.DataFrame(
            {
                "Note": [ABOUT_NOTE],
                "Project": [project_name],
                "Demo data": ["yes" if is_demo else "no"],
            }
        )
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            frame.to_excel(writer, index=False, sheet_name="TestCases")
            about.to_excel(writer, index=False, sheet_name="About")
        return (
            buffer.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            _filename(project_name, "xlsx"),
        )
    if fmt == "json":
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "project": {"id": project_id, "name": project_name, "is_demo": is_demo},
            "note": ABOUT_NOTE,
            "test_cases": cases,
        }
        data = json.dumps(payload, indent=2, default=str).encode("utf-8")
        return data, "application/json", _filename(project_name, "json")
    raise ValueError(f"Unsupported export format '{fmt}'")
