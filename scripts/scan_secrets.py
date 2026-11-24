#!/usr/bin/env python3
"""Scan the repository for high-risk credential patterns.

Placeholders in .env.example are allowed. Matches are printed and the process
exits with status 1 when a likely secret is found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "data", "playwright-report", "test-results"}
PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"gho_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"),
]
ALLOW_LINE = re.compile(r"OPENAI_API_KEY=\s*$|ANTHROPIC_API_KEY=\s*$|your-key-here|sk-local-test-value")


def main() -> int:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".xlsx", ".db", ".sqlite"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if ALLOW_LINE.search(line):
                continue
            for pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(f"{path.relative_to(ROOT)}:{number}: {pattern.pattern}")
    if findings:
        print("Possible secrets:")
        print("\n".join(findings))
        return 1
    print("No high-risk credential patterns found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
