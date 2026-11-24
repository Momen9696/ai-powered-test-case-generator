"""Heuristic requirements analysis.

Every finding is marked extracted or inferred.
Extracted findings quote the source. Inferred findings are gaps or suggestions
and are not presented as facts stated by the author.
This module does not call a language model.
"""

from __future__ import annotations

import hashlib
import re

from app.schemas import Finding

AMBIGUOUS_TERMS = [
    "as soon as possible",
    "user-friendly",
    "user friendly",
    "and/or",
    "as needed",
    "a few",
    "intuitive",
    "appropriate",
    "reasonable",
    "seamless",
    "scalable",
    "robust",
    "adequate",
    "several",
    "various",
    "quickly",
    "proper",
    "asap",
    "fast",
    "soon",
    "tbd",
    "tba",
    "tbc",
    "etc",
]

_AC_HEADING = re.compile(
    r"^(acceptance criteria|acceptance tests|acceptance conditions)\s*:?\s*$",
    re.IGNORECASE,
)
_BULLET = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(.*\S)\s*$")
_ACTOR_STORY = re.compile(
    r"\bAs an?\s+([A-Za-z][A-Za-z \-/]{1,40}?)(?:,|\s+I\s+want\b)",
    re.IGNORECASE,
)
_GOAL = re.compile(
    r"\bI want to\s+(.+?)(?:\s+so that\b|[.]|$)",
    re.IGNORECASE,
)
_RANGE = re.compile(
    r"between\s+([0-9]+(?:\.[0-9]+)?)\s+and\s+([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]{0,12})?",
    re.IGNORECASE,
)
_LIMIT = re.compile(
    r"(?:daily limit of|limit of|at most|no more than|up to)\s+([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]{0,12})?",
    re.IGNORECASE,
)
_RULE = re.compile(
    r"\b(shall|must|must not|cannot|may not|only if|rejected|reject|at least|at most)\b",
    re.IGNORECASE,
)
_DEPENDENCY = re.compile(
    r"\b(depends on|integrates with|requires|third-party|webhook)\b",
    re.IGNORECASE,
)
_GIVEN = re.compile(r"^\s*given\b", re.IGNORECASE)
_THEN = re.compile(r"\bthen\b\s+(.*)", re.IGNORECASE)
_OUTCOME = re.compile(
    r"\b(shows?|displays?|confirmation|status|does not change|do not change)\b",
    re.IGNORECASE,
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [_norm(part) for part in parts if _norm(part)]


def _finding(
    prefix: str,
    number: int,
    statement: str,
    origin: str,
    evidence: str | None = None,
    rationale: str | None = None,
) -> dict:
    return Finding(
        id=f"{prefix}-{number}",
        statement=statement,
        origin=origin,  # type: ignore[arg-type]
        evidence=evidence,
        rationale=rationale,
    ).model_dump()


def _acceptance_criteria(text: str) -> list[dict]:
    lines = text.splitlines()
    collected: list[str] = []
    in_section = False
    saw_heading = False
    for line in lines:
        if _AC_HEADING.match(line.strip()):
            in_section = True
            saw_heading = True
            continue
        if in_section:
            if not line.strip():
                if collected:
                    in_section = False
                continue
            if line.strip().endswith(":") and not _BULLET.match(line):
                in_section = False
                continue
            match = _BULLET.match(line)
            if match:
                collected.append(_norm(match.group(1)))
                continue
            if collected:
                in_section = False
    if not saw_heading:
        for line in lines:
            match = _BULLET.match(line)
            if not match:
                continue
            statement = _norm(match.group(1))
            if re.search(r"\b(shall|must|can|should|when|then)\b", statement, re.IGNORECASE):
                collected.append(statement)
    # Given/When/Then lines that were not already captured.
    for sentence in _sentences(text):
        if sentence.lower().startswith("given ") and " when " in sentence.lower():
            if sentence not in collected:
                collected.append(sentence)
    findings = []
    for index, statement in enumerate(collected, start=1):
        findings.append(
            _finding(
                "AC",
                index,
                statement,
                "extracted",
                evidence=statement,
                rationale="Captured from an acceptance criterion or a Given/When/Then statement.",
            )
        )
    return findings


def _ambiguities(text: str) -> list[dict]:
    findings = []
    seen: set[str] = set()
    for sentence in _sentences(text):
        lowered = sentence.lower()
        for term in AMBIGUOUS_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", lowered):
                key = (term, lowered)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(
                    _finding(
                        "AMB",
                        len(findings) + 1,
                        f"Ambiguous term '{term}' makes the statement hard to test as written.",
                        "extracted",
                        evidence=sentence,
                        rationale=(
                            "The quoted sentence appears in the source. "
                            "The ambiguity label is a heuristic match on a non-measurable term."
                        ),
                    )
                )
    return findings


def analyze_requirements(text: str, kind: str = "user_story") -> dict:
    """Return a deterministic analysis payload for the given text."""
    cleaned = text.strip()
    actors: list[dict] = []
    for match in _ACTOR_STORY.finditer(cleaned):
        name = _norm(match.group(1))
        actors.append(
            _finding("ACT", len(actors) + 1, name, "extracted", evidence=match.group(0).strip())
        )
    for line in cleaned.splitlines():
        role_match = re.match(
            r"^\s*[-*]\s*([A-Za-z][A-Za-z ]{0,40}?)\s+(submits|approves|rejects|creates)\b",
            line,
        )
        if role_match:
            name = role_match.group(1).strip()
            if not any(item["statement"].lower() == name.lower() for item in actors):
                actors.append(
                    _finding(
                        "ACT",
                        len(actors) + 1,
                        name,
                        "extracted",
                        evidence=line.strip(),
                        rationale="Role named in the source.",
                    )
                )

    functional: list[dict] = []
    for match in _GOAL.finditer(cleaned):
        functional.append(
            _finding(
                "FR",
                len(functional) + 1,
                _norm(match.group(1)),
                "extracted",
                evidence=match.group(0).strip(),
                rationale="Taken from the user-story goal.",
            )
        )
    for line in cleaned.splitlines():
        if re.search(r"\bthe system shall\b", line, re.IGNORECASE):
            statement = _norm(line)
            functional.append(
                _finding(
                    "FR",
                    len(functional) + 1,
                    statement,
                    "extracted",
                    evidence=statement,
                )
            )

    business_rules = []
    for sentence in _sentences(cleaned):
        if _RULE.search(sentence):
            business_rules.append(
                _finding(
                    "BR",
                    len(business_rules) + 1,
                    sentence,
                    "extracted",
                    evidence=sentence,
                    rationale="Sentence uses obligation, limit, or rejection language.",
                )
            )

    preconditions = []
    for sentence in _sentences(cleaned):
        if _GIVEN.match(sentence):
            preconditions.append(
                _finding("PRE", len(preconditions) + 1, sentence, "extracted", evidence=sentence)
            )

    outcomes = []
    for sentence in _sentences(cleaned):
        then_match = _THEN.search(sentence)
        if then_match:
            outcomes.append(
                _finding(
                    "OUT",
                    len(outcomes) + 1,
                    _norm(then_match.group(1)),
                    "extracted",
                    evidence=sentence,
                )
            )
        elif _OUTCOME.search(sentence) and not sentence.lower().startswith("as a"):
            outcomes.append(
                _finding("OUT", len(outcomes) + 1, sentence, "extracted", evidence=sentence)
            )

    constraints = []
    for match in _RANGE.finditer(cleaned):
        unit = match.group(3) or ""
        statement = f"Allowed range is {match.group(1)} to {match.group(2)} {unit}".strip()
        constraints.append(
            _finding("CON", len(constraints) + 1, statement, "extracted", evidence=match.group(0))
        )
    for match in _LIMIT.finditer(cleaned):
        unit = match.group(2) or ""
        statement = f"Stated limit is {match.group(1)} {unit}".strip()
        constraints.append(
            _finding("CON", len(constraints) + 1, statement, "extracted", evidence=match.group(0))
        )

    dependencies = []
    for sentence in _sentences(cleaned):
        if _DEPENDENCY.search(sentence):
            dependencies.append(
                _finding("DEP", len(dependencies) + 1, sentence, "extracted", evidence=sentence)
            )

    acceptance = _acceptance_criteria(cleaned)
    ambiguities = _ambiguities(cleaned)

    missing: list[dict] = []

    def add_missing(statement: str, rationale: str) -> None:
        missing.append(
            _finding("MISS", len(missing) + 1, statement, "inferred", rationale=rationale)
        )

    if len(cleaned) < 40:
        add_missing(
            "The input is too short to derive testable acceptance criteria.",
            "Fewer than 40 characters of source text were provided.",
        )
    if not actors:
        add_missing(
            "No actor or role was named.",
            "No 'As a <role>' clause or role bullet was found.",
        )
    if not acceptance:
        add_missing(
            "No acceptance criteria were stated.",
            "No acceptance-criteria section, qualifying bullet, or Given/When/Then statement was found.",
        )
    if not preconditions:
        add_missing(
            "No explicit preconditions were stated.",
            "No Given clause or prerequisite line was found. A tester would have to assume setup.",
        )
    if not re.search(r"\b(error|reject|invalid|insufficient|fail)\b", cleaned, re.IGNORECASE):
        add_missing(
            "No error or rejection behavior was stated.",
            "The source does not say what the system does with invalid input or failed dependencies.",
        )
    if not re.search(r"\b(auth|login|permission|role|only if|unauthori[sz]ed)\b", cleaned, re.IGNORECASE):
        add_missing(
            "Authentication and authorization rules were not stated.",
            "The source does not say who may perform the action or how they sign in.",
        )
    if re.search(r"\b(amount|limit|quantity|balance)\b", cleaned, re.IGNORECASE) and not constraints:
        add_missing(
            "Amounts or limits are mentioned without a numeric boundary.",
            "A boundary-value test needs an explicit minimum or maximum.",
        )

    digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
    return {
        "summary": {
            "input_kind": kind,
            "character_count": len(cleaned),
            "content_sha256": digest,
            "detector": "heuristic-v1",
            "llm_used": False,
            "note": (
                "Extracted items quote the source. "
                "Inferred items are gaps identified by deterministic rules, not by a language model."
            ),
        },
        "functional_requirements": functional,
        "business_rules": business_rules,
        "actors": actors,
        "preconditions": preconditions,
        "expected_outcomes": outcomes,
        "constraints": constraints,
        "missing_information": missing,
        "ambiguities": ambiguities,
        "dependencies": dependencies,
        "acceptance_criteria": acceptance,
    }
