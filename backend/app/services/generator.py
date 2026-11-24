"""Build structured test cases from an analysis payload.

The builder is deterministic. Scenario origin is extracted when the source
states the behavior, and inferred when the case is a testing suggestion.
"""

from __future__ import annotations

import re

from app.schemas import ALL_TEST_TYPES

_REJECTION = re.compile(
    r"\b(reject|rejected|error|invalid|insufficient|must not|cannot|do not change|does not change)\b",
    re.IGNORECASE,
)
_RANGE = re.compile(
    r"between\s+([0-9]+(?:\.[0-9]+)?)\s+and\s+([0-9]+(?:\.[0-9]+)?)(?:\s+([A-Za-z]{1,12}))?",
    re.IGNORECASE,
)
_LIMIT = re.compile(
    r"(?:limit of|at most|no more than|up to)\s+([0-9]+(?:\.[0-9]+)?)(?:\s+([A-Za-z]{1,12}))?",
    re.IGNORECASE,
)
_SENSITIVE = re.compile(
    r"\b(transfer|payment|balance|funds|limit|invoice|approve|password|auth)\b",
    re.IGNORECASE,
)
_API = re.compile(r"\b(api|endpoint|json|http|rest)\b", re.IGNORECASE)
_UI = re.compile(r"\b(page|screen|button|form|click|dashboard|field)\b", re.IGNORECASE)
_SECURITY = re.compile(r"\b(auth|permission|password|unauthori[sz]ed|role|only if)\b", re.IGNORECASE)


def _clip(text: str, words: int = 14) -> str:
    parts = re.sub(r"\s+", " ", text).strip().split(" ")
    clipped = " ".join(parts[:words]).rstrip(".,;:")
    return clipped or "the requirement"


def _priority(test_type: str, text: str) -> tuple[str, str]:
    sensitive = bool(_SENSITIVE.search(text))
    if test_type == "security":
        return ("high", "high")
    if test_type in {"negative", "error_handling", "boundary"}:
        return ("high", "high" if sensitive else "medium")
    if test_type in {"functional", "positive", "api"} and sensitive:
        return ("high", "medium")
    if test_type == "edge":
        return ("medium", "medium")
    if test_type == "ui":
        return ("medium", "low")
    return ("medium", "low")


def _automation(test_type: str) -> str:
    return {
        "api": "high",
        "functional": "high",
        "positive": "high",
        "negative": "high",
        "boundary": "high",
        "error_handling": "medium",
        "security": "medium",
        "ui": "medium",
        "edge": "low",
    }.get(test_type, "medium")


def _case(
    *,
    title: str,
    description: str,
    requirement_ref: str,
    preconditions: list[str],
    steps: list[str],
    test_data: dict[str, str],
    expected_result: str,
    test_type: str,
    scenario_origin: str,
    source_text: str,
    extra_tags: list[str] | None = None,
) -> dict:
    priority, risk = _priority(test_type, f"{title} {source_text}")
    tags = [test_type, scenario_origin]
    if extra_tags:
        for tag in extra_tags:
            if tag not in tags:
                tags.append(tag)
    return {
        "title": title[:300],
        "description": description,
        "requirement_ref": requirement_ref,
        "preconditions": preconditions,
        "steps": steps,
        "test_data": test_data,
        "expected_result": expected_result,
        "test_type": test_type,
        "priority": priority,
        "risk_level": risk,
        "automation_suitability": _automation(test_type),
        "tags": tags,
        "scenario_origin": scenario_origin,
    }


def _actor_name(analysis: dict) -> str | None:
    actors = analysis.get("actors") or []
    if not actors:
        return None
    return str(actors[0].get("statement") or "").strip() or None


def _preconditions(actor: str | None, explicit: list[dict]) -> list[str]:
    items = [item["statement"] for item in explicit[:3] if item.get("statement")]
    if actor:
        items.insert(0, f"The actor '{actor}' can reach the feature under test.")
    else:
        items.append("A tester can reach the feature under test.")
    return items


def _selected(selected_types: list[str] | None) -> set[str]:
    if not selected_types:
        return set(ALL_TEST_TYPES)
    return set(selected_types)


def build_cases(source_text: str, analysis: dict, selected_types: list[str] | None = None) -> list[dict]:
    wanted = _selected(selected_types)
    criteria = list(analysis.get("acceptance_criteria") or [])
    actor = _actor_name(analysis)
    explicit_pre = list(analysis.get("preconditions") or [])
    base_pre = _preconditions(actor, explicit_pre)
    if not criteria:
        first = next((line.strip() for line in source_text.splitlines() if line.strip()), "")
        criteria = [
            {
                "id": "REQ-UNSPECIFIED",
                "statement": first[:240] or "The requirement text did not state a testable criterion.",
                "origin": "inferred",
            }
        ]

    cases: list[dict] = []
    for criterion in criteria:
        ref = str(criterion.get("id") or "REQ-UNSPECIFIED")
        statement = str(criterion.get("statement") or "").strip()
        origin = "extracted" if criterion.get("origin") == "extracted" else "inferred"
        short = _clip(statement)
        rejection = bool(_REJECTION.search(statement))
        who = actor or "the user"

        if "functional" in wanted:
            cases.append(
                _case(
                    title=f"Verify {short}",
                    description=(
                        f"Functional check for {ref}. "
                        "Steps restate the criterion and add execution setup."
                    ),
                    requirement_ref=ref,
                    preconditions=base_pre,
                    steps=[
                        f"Open the flow as {who}.",
                        f"Use inputs that match this criterion: {statement}",
                        "Submit the action once and record the response.",
                    ],
                    test_data={"criterion": statement},
                    expected_result=(
                        "The system behaves as the criterion states, and the observable result is recorded."
                    ),
                    test_type="functional",
                    scenario_origin=origin,
                    source_text=source_text,
                )
            )

        if "positive" in wanted and not rejection:
            cases.append(
                _case(
                    title=f"Accept the valid path for {short}",
                    description=f"Positive scenario grounded in {ref}.",
                    requirement_ref=ref,
                    preconditions=base_pre,
                    steps=[
                        f"Prepare valid data for: {statement}",
                        f"Perform the action as {who}.",
                        "Confirm the success response and any persisted change.",
                    ],
                    test_data={"path": "valid"},
                    expected_result="The valid action is accepted and the stated outcome is visible.",
                    test_type="positive",
                    scenario_origin=origin,
                    source_text=source_text,
                )
            )

        if "negative" in wanted and rejection:
            cases.append(
                _case(
                    title=f"Reject the guarded path for {short}",
                    description=f"Negative scenario stated by {ref}.",
                    requirement_ref=ref,
                    preconditions=base_pre,
                    steps=[
                        f"Prepare the condition described here: {statement}",
                        "Submit the action.",
                        "Check that protected data did not change.",
                    ],
                    test_data={"path": "rejected"},
                    expected_result=(
                        "The system rejects the action with a clear error and does not apply the protected change."
                    ),
                    test_type="negative",
                    scenario_origin=origin,
                    source_text=source_text,
                )
            )

        range_match = _RANGE.search(statement)
        limit_match = _LIMIT.search(statement)
        if "boundary" in wanted and (range_match or limit_match):
            if range_match:
                low, high, unit = range_match.group(1), range_match.group(2), range_match.group(3) or ""
                data = {
                    "minimum": low,
                    "maximum": high,
                    "unit": unit,
                }
                inside_expected = f"Values {low} and {high} {unit} are accepted when the rest of the input is valid."
            else:
                high = limit_match.group(1) if limit_match else ""
                unit = limit_match.group(2) if limit_match else ""
                low = ""
                data = {"stated_limit": high, "unit": unit or ""}
                inside_expected = f"A value at the stated limit of {high} {unit} follows the written rule."
            cases.append(
                _case(
                    title=f"Boundary values stated for {short}",
                    description=f"Boundary points taken from the numbers in {ref}.",
                    requirement_ref=ref,
                    preconditions=base_pre,
                    steps=[
                        "Submit the stated minimum or limit value when one is written.",
                        "Submit the stated maximum when a range is written.",
                        "Record acceptance or rejection for each stated boundary.",
                    ],
                    test_data=data,
                    expected_result=inside_expected.strip(),
                    test_type="boundary",
                    scenario_origin="extracted",
                    source_text=source_text,
                    extra_tags=["boundary-stated"],
                )
            )
            outside = dict(data)
            if low:
                outside["just_below_minimum"] = "below the stated minimum by the smallest unit"
            if high:
                outside["just_above_maximum_or_limit"] = "above the stated maximum or limit by the smallest unit"
            cases.append(
                _case(
                    title=f"Values outside the stated boundary for {short}",
                    description=(
                        "Outside points are a boundary-value suggestion. "
                        "The source states the range or limit, not the off-by-one result."
                    ),
                    requirement_ref=ref,
                    preconditions=base_pre,
                    steps=[
                        "Submit a value one unit outside the stated range or limit.",
                        "Record the error text and whether data changed.",
                    ],
                    test_data=outside,
                    expected_result=(
                        "The value outside the stated range or limit is rejected. "
                        "This expected result is inferred from boundary-value analysis."
                    ),
                    test_type="boundary",
                    scenario_origin="inferred",
                    source_text=source_text,
                    extra_tags=["boundary-outside"],
                )
            )

    # Document-level suggestions, one of each, so the suite stays reviewable.
    focus = _clip(criteria[0]["statement"])
    ref = str(criteria[0].get("id") or "REQ-UNSPECIFIED")
    security_origin = "extracted" if _SECURITY.search(source_text) else "inferred"
    api_origin = "extracted" if _API.search(source_text) else "inferred"
    ui_origin = "extracted" if _UI.search(source_text) else "inferred"
    error_origin = (
        "extracted"
        if re.search(r"\b(error|reject|invalid|insufficient|fail)\b", source_text, re.IGNORECASE)
        else "inferred"
    )

    if "negative" in wanted and not any(case["test_type"] == "negative" for case in cases):
        cases.append(
            _case(
                title=f"Reject an unauthorized attempt related to {focus}",
                description="The source does not state an authorization rule. This case is a suggestion.",
                requirement_ref=ref,
                preconditions=base_pre + ["A second actor without the required permission is available."],
                steps=[
                    "Sign in as an actor who should not perform the action, if such a role exists.",
                    "Attempt the primary action.",
                    "Confirm the system refuses the action.",
                ],
                test_data={"actor": "unauthorized"},
                expected_result="The action is refused. The expected refusal is inferred because the source did not state it.",
                test_type="negative",
                scenario_origin="inferred",
                source_text=source_text,
            )
        )

    if "edge" in wanted:
        cases.append(
            _case(
                title=f"Edge inputs around {focus}",
                description="Empty, blank, and oversized inputs. These values are not quoted from the source.",
                requirement_ref=ref,
                preconditions=base_pre,
                steps=[
                    "Submit the primary field empty.",
                    "Submit the primary field as whitespace only.",
                    "Submit a value far longer than a tester would expect a user to enter.",
                ],
                test_data={"empty": "", "whitespace": " ", "oversized": "x" * 32},
                expected_result="The system rejects empty or oversized input with a validation message and leaves stored data unchanged.",
                test_type="edge",
                scenario_origin="inferred",
                source_text=source_text,
            )
        )

    if "error_handling" in wanted:
        cases.append(
            _case(
                title=f"Error handling while completing {focus}",
                description=(
                    "Checks a failure during the action."
                    if error_origin == "extracted"
                    else "The source does not describe dependency failure. This case is a suggestion."
                ),
                requirement_ref=ref,
                preconditions=base_pre,
                steps=[
                    "Start the primary action with otherwise valid data.",
                    "Cause a dependent save or notification step to fail, if the environment can simulate that.",
                    "Observe the message shown to the actor and the final stored state.",
                ],
                test_data={"fault": "dependent step unavailable"},
                expected_result=(
                    "The actor sees an error and partial changes are not left in an ambiguous state."
                ),
                test_type="error_handling",
                scenario_origin=error_origin,
                source_text=source_text,
            )
        )

    if "security" in wanted:
        cases.append(
            _case(
                title=f"Security checks around {focus}",
                description=(
                    "Security-oriented suggestions. These are review prompts, not a penetration test."
                ),
                requirement_ref=ref,
                preconditions=base_pre,
                steps=[
                    "Attempt the action without a session, or with a session for another owner.",
                    "Submit a field value that contains script or query metacharacters as plain data.",
                    "Confirm the response does not expose another actor's data.",
                ],
                test_data={"payload_sample": "<script>alert(1)</script>", "other_owner": "second-account"},
                expected_result=(
                    "The system keeps the actor inside their own data and treats metacharacters as data, not as commands."
                ),
                test_type="security",
                scenario_origin=security_origin,
                source_text=source_text,
                extra_tags=["suggestion"],
            )
        )

    if "api" in wanted:
        cases.append(
            _case(
                title=f"API scenario for {focus}",
                description=(
                    "API checks suggested for the same rule. "
                    + (
                        "The source mentions an API-style interface."
                        if api_origin == "extracted"
                        else "The source does not mention an API. This case is a suggestion."
                    )
                ),
                requirement_ref=ref,
                preconditions=base_pre + ["An API client and test account are available."],
                steps=[
                    "Send a valid request that represents the criterion.",
                    "Send the same request with a missing required field.",
                    "Compare the status code, error body, and stored state.",
                ],
                test_data={"method": "POST", "auth": "bearer token for the actor"},
                expected_result="The valid request matches the criterion. The invalid request is rejected without a partial write.",
                test_type="api",
                scenario_origin=api_origin,
                source_text=source_text,
                extra_tags=["suggestion"] if api_origin == "inferred" else ["api"],
            )
        )

    if "ui" in wanted:
        cases.append(
            _case(
                title=f"UI scenario for {focus}",
                description=(
                    "UI checks for the same rule. "
                    + (
                        "The source mentions a screen or control."
                        if ui_origin == "extracted"
                        else "The source does not describe a screen. This case is a suggestion."
                    )
                ),
                requirement_ref=ref,
                preconditions=base_pre,
                steps=[
                    "Open the screen a user would use for this action.",
                    "Enter the data from the criterion and submit.",
                    "Check labels, the confirmation or error text, and that the control cannot be submitted twice by a double click.",
                ],
                test_data={"client": "desktop browser"},
                expected_result="The screen shows the same acceptance or rejection the requirement describes, in language the user can act on.",
                test_type="ui",
                scenario_origin=ui_origin,
                source_text=source_text,
                extra_tags=["suggestion"] if ui_origin == "inferred" else ["ui"],
            )
        )

    return cases
