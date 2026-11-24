# Case study

## Overview

Test Case Generator is a local application for turning written requirements into a suite a QA engineer can edit, map, and export. The repository is a portfolio implementation. It was not measured against a production client's defect rate.

## Problem

Teams often draft test cases in a spreadsheet after reading a story once. The spreadsheet then loses the link to the acceptance criterion, mixes happy paths with unstated security ideas, and cannot show which sentences were too vague to test.

A model can draft cases, but a demo that only works with a paid key is hard to review, and a demo that invents a quality score misrepresents the output.

## Approach

The API stores the source text, a heuristic analysis, and the generated cases. Every analysis item is marked extracted or inferred. Extracted items keep a quote. Inferred items are gaps, such as missing acceptance criteria or missing error behavior.

The default generator is deterministic. The same story produces the same cases, which makes the suite testable in CI. OpenAI and Anthropic adapters use the same JSON schema and a single repair attempt, and they stay off unless a server-side key exists.

The UI is a working dashboard: projects, generation, analysis, an editable case table, suites, export, and settings. Counts on the dashboard come from SQLite.

## Verification

Backend pytest, frontend Vitest, a production build, and a Playwright walkthrough of generation and export are part of the repository. The execution report in `docs/execution/TEST-RESULTS.md` records the commands that were run for this checkout. Screenshots in `docs/screenshots/` were captured from that running UI.

## Business value

- A reviewer can see which cases restate the story and which cases are suggestions.
- Coverage is a mapping from acceptance-criterion ids to stored cases, so an uncovered criterion stays visible.
- Excel, CSV, and JSON exports give the suite to people who will not use the app.
- The mock provider lets a team try the workflow on a laptop without an API account.

## Use cases

- Draft a first suite from a user story before a refinement meeting.
- Check a requirements page for vague terms and missing error behavior.
- Keep positive, negative, and boundary cases tied to the same criterion id.
- Hand an export to an automation engineer as a starting backlog, not as an executed run.

## What this does not claim

- It does not execute the generated steps.
- It does not replace a penetration test. Security rows are suggestions.
- It does not report a model accuracy score.
- It does not authenticate users. It is a local tool.
