# Upwork portfolio description

## Title

AI test case generator — requirements in, reviewable suites out

## Description

I built a local web application that turns user stories and requirements documents into structured test cases a QA team can review, edit, and export.

The API is FastAPI, Pydantic, and SQLAlchemy on SQLite. The UI is React, TypeScript, and Material UI. Generation goes through a provider interface. The default provider is a deterministic mock, so the product runs in CI and in a demo without an OpenAI or Anthropic key. Optional adapters call those APIs only when a server environment variable is set. Keys are not accepted from the browser.

The analyzer separates extracted statements from inferred gaps. It pulls actors, business rules, constraints, dependencies, and acceptance criteria, and it flags vague wording and missing criteria. Generated cases cover functional, positive, negative, boundary, edge, error-handling, security, API, and UI scenarios. Each case keeps its requirement id, steps, data, priority, risk, and automation suitability.

Reviewers can edit cases, group them into suites, filter the table, and see which acceptance criteria have no case yet. Duplicate titles are flagged with a lexical similarity check, not a made-up model score. Export writes Excel, CSV, and JSON, and the file states when rows came from the mock provider.

Pytest covers analysis, generation, the API, exports, invalid model output, and upload rejection. Vitest covers validation, filtering, and the main screens. Playwright walks through generation and export. Docker Compose and GitHub Actions are included.

The app is a single-user local tool. It does not execute generated tests and it does not pretend the mock output came from a live model.

## Profile summary line

I design QA tools that turn requirements into traceable, exportable test suites, with a mock mode that demos cleanly and adapters for real model APIs.
