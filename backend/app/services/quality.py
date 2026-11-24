"""Duplicate detection and coverage mapping.

Duplicate detection compares titles with token Jaccard similarity.
It is a lexical check, not an embedding or a model score.
Coverage counts acceptance criteria that at least one stored case references.
"""

from __future__ import annotations

import re


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _clusters(cases: list[dict], threshold: float) -> tuple[list[list[int]], dict[tuple[int, int], float]]:
    parent = list(range(len(cases)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    scores: dict[tuple[int, int], float] = {}
    token_sets = [tokens(str(case.get("title") or "")) for case in cases]
    for i in range(len(cases)):
        for j in range(i + 1, len(cases)):
            score = jaccard(token_sets[i], token_sets[j])
            if score >= threshold:
                union(i, j)
                scores[(i, j)] = round(score, 3)
    grouped: dict[int, list[int]] = {}
    for index in range(len(cases)):
        grouped.setdefault(find(index), []).append(index)
    clusters = [indexes for indexes in grouped.values() if len(indexes) >= 2]
    return clusters, scores


def find_duplicate_groups(cases: list[dict], threshold: float = 0.8) -> list[dict]:
    clusters, scores = _clusters(cases, threshold)
    groups = []
    for indexes in clusters:
        pair_scores = [scores[(a, b)] for a in indexes for b in indexes if a < b and (a, b) in scores]
        groups.append(
            {
                "method": "token_jaccard",
                "threshold": threshold,
                "score": max(pair_scores) if pair_scores else threshold,
                "cases": [
                    {
                        "id": cases[index].get("id"),
                        "case_key": cases[index].get("case_key"),
                        "title": cases[index].get("title"),
                    }
                    for index in indexes
                ],
            }
        )
    groups.sort(key=lambda item: item["score"], reverse=True)
    return groups


def flag_duplicates(cases: list[dict], threshold: float = 0.8) -> list[dict]:
    """Return the same cases with duplicate tags when titles are near copies."""
    clusters, _scores = _clusters(cases, threshold)
    partner: dict[int, str] = {}
    for indexes in clusters:
        for index in indexes:
            others = [cases[other]["title"] for other in indexes if other != index]
            partner[index] = others[0] if others else cases[index]["title"]
    updated = []
    for index, case in enumerate(cases):
        copied = dict(case)
        if index in partner:
            tags = list(copied.get("tags") or [])
            if "possible-duplicate" not in tags:
                tags.append("possible-duplicate")
            copied["tags"] = tags
            copied["possible_duplicate_of"] = partner[index]
        updated.append(copied)
    return updated


def coverage_report(analysis: dict | None, cases: list[dict]) -> dict:
    criteria = list((analysis or {}).get("acceptance_criteria") or [])
    items = []
    for criterion in criteria:
        ref = criterion.get("id")
        matched = [
            {
                "id": case.get("id"),
                "case_key": case.get("case_key"),
                "title": case.get("title"),
                "test_type": case.get("test_type"),
            }
            for case in cases
            if case.get("requirement_ref") == ref
        ]
        items.append(
            {
                "id": ref,
                "statement": criterion.get("statement"),
                "origin": criterion.get("origin"),
                "covered": bool(matched),
                "cases": matched,
            }
        )
    total = len(items)
    covered = sum(1 for item in items if item["covered"])
    return {
        "basis": "An acceptance criterion is covered when a stored test case uses its id as requirement_ref.",
        "detector": "reference-mapping-v1",
        "llm_used": False,
        "total_acceptance_criteria": total,
        "covered": covered,
        "coverage_percent": round(100.0 * covered / total, 1) if total else None,
        "items": items,
        "uncovered": [item for item in items if not item["covered"]],
        "note": None
        if total
        else "No acceptance criteria were extracted, so a coverage percentage is not shown.",
    }
