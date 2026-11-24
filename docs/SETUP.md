# Setup

## Requirements

- Python 3.12 or 3.13
- Node.js 22
- Optional: Docker Compose v2

## API

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The database file is `backend/data/app.db`. Delete that file to reset local data.

Apply the Alembic revision explicitly if you want the migration history recorded:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Startup already creates tables, so this step is optional for local use.

## UI

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8000`.

## Tests

```bash
cd backend && .venv/bin/pytest
cd frontend && npm test
cd frontend && npm run build
cd frontend && npm run e2e
```

Playwright starts the API and Vite. Install Chromium once with `npx playwright install chromium` inside `frontend`.

## Docker

```bash
docker compose up --build
```

- UI: http://localhost:8080
- API: http://localhost:8000/docs

SQLite data stays in the `appdata` volume.

## Optional model providers

Set the key in the environment of the API process, then choose the provider in Settings:

```bash
export OPENAI_API_KEY=...
```

or

```bash
export ANTHROPIC_API_KEY=...
```

Do not put a real key in `.env` and commit it. `.gitignore` excludes `.env`.
