# Execution report

Recorded on 2026-11-24 from this checkout. Commands were run on the machine that produced the repository. Figures below are the command output, not estimates.

## Backend

```text
cd backend && .venv/bin/pytest -q
................................                                         [100%]
32 passed
```

Coverage of the suite includes analysis, deterministic generation, duplicate grouping, requirement mapping, the HTTP API, Excel/CSV/JSON exports, upload rejection, secret redaction, invalid provider output plus one repair attempt, and the Alembic upgrade.

## Frontend

```text
cd frontend && npm test
Test Files  6 passed (6)
Tests       11 passed (11)
```

```text
cd frontend && npm run build
tsc --noEmit && vite build
built in ~1s
```

```text
cd frontend && npm run e2e
2 passed (8.2s)
```

The Playwright run started the API and Vite, created a project from a user story, opened the generated table, downloaded JSON, and saved the screenshots in `docs/screenshots/`.

## Dependency and secret scans

- `pip-audit -r backend/requirements.txt`: no known vulnerabilities after upgrading FastAPI, Starlette, python-multipart, and pytest.
- `npm audit` after installing Vitest 4.1.12: 0 vulnerabilities.
- `python3 scripts/scan_secrets.py`: no high-risk credential patterns found.

## Docker

The Docker CLI is not installed on the machine used for this run, so `docker compose up` was not executed. `docker-compose.yml`, both Dockerfiles, and the nginx proxy were reviewed. GitHub Actions runs `docker compose config` on Ubuntu, where the Docker CLI is available.

## Browser check

With the API on port 8000 and Vite on port 5173, the dashboard showed the seeded demo project: 17 stored cases, 1 suite, coverage 4 of 4, and the latest run labeled `mock / deterministic-rules-v1`. The test-case table listed TC-0001 through TC-0017. Opening TC-0009 showed the extracted functional case for the confirmation-number criterion. Settings showed provider `mock (ready)` and did not display an API key.
