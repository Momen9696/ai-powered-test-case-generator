# AI-Powered Test Case Generator

[![CI](https://github.com/Momen9696/ai-powered-test-case-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/Momen9696/ai-powered-test-case-generator/actions/workflows/ci.yml)

A local web application that turns a user story or a requirements document into reviewable test cases. The default provider is a deterministic rules engine. It does not call a paid API, and the interface does not present its output as a language-model score.

Optional OpenAI and Anthropic adapters are included. They run only when a key is set in the server environment and the provider is selected in Settings.

## What you can do

- Paste a user story or a requirements document, or upload a `.txt`, `.md`, or `.csv` file.
- Separate extracted statements from inferred gaps.
- Generate functional, positive, negative, boundary, edge, error-handling, security, API, and UI scenarios.
- Edit cases, organize suites, and search, filter, and sort the table.
- Map test cases back to acceptance-criteria ids.
- Flag near-duplicate titles with token Jaccard similarity.
- Export Excel, CSV, and JSON.

## Stack

| Area | Choice |
| --- | --- |
| API | Python, FastAPI, Pydantic v2, SQLAlchemy, SQLite |
| Tests | Pytest, Vitest, Testing Library, Playwright |
| UI | React, TypeScript, Vite, Material UI |
| Export | Pandas and OpenPyXL |
| Run | Docker Compose, GitHub Actions |

## Run it locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). API docs are at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

```bash
cd frontend   # from the repo root, in another shell the backend is already running
npm test
npm run build
npm run e2e
```

From the repo root, `make test` runs the backend and frontend unit tests when the virtualenv and `node_modules` are already installed.

Docker:

```bash
docker compose up --build
```

The UI is then at [http://localhost:8080](http://localhost:8080).

Copy `.env.example` to `.env` only if you need overrides. Leave the API keys empty to stay on the mock provider.

## Mock mode

The mock provider (`deterministic-rules-v1`) builds cases from the analysis payload. The same text produces the same cases. Temperature is stored and ignored. Token figures are character-count estimates and are labeled that way. Exports say when a row came from the mock provider.

There is no quality score, confidence percentage, or claim that a mock run used GPT or Claude.

## Documentation

- [Setup](docs/SETUP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API](docs/API.md)
- [User guide](docs/USER_GUIDE.md)
- [Example stories](examples/user-stories.md)
- [Example suite](examples/sample-suite.json)
- [Execution report](docs/execution/TEST-RESULTS.md)
- [Case study](docs/portfolio/case-study.md)

## Security notes

This is a single-operator local tool. It does not ship login. Do not expose it to the public internet without an authentication layer in front of it.

Uploaded files are read as UTF-8 text and stored in SQLite. The process does not write the upload to disk and does not execute requirement text. Keys are environment variables and are not returned by `/api/settings`.

## Limitations

- The analyzer is an English heuristic, not a general parser.
- Duplicate detection compares titles. It does not use embeddings.
- Coverage means "a case references this acceptance-criterion id." It is not execution coverage.
- Remote providers are adapters. CI does not call them.
- SQLite is the supported database for local setup and Docker.
