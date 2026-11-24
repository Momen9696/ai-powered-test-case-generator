# API

Interactive schemas are served at `/docs` and `/openapi.json`.

All paths below are under the API origin.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Process and active provider |
| GET | `/api/examples` | Built-in requirement examples |
| GET, PUT | `/api/settings` | Provider, model override, temperature, max tokens |
| POST | `/api/demo/seed` | Create or return the labeled demo project |
| GET, POST | `/api/projects` | List or create projects |
| GET, DELETE | `/api/projects/{id}` | Read or delete a project |
| GET | `/api/projects/{id}/summary` | Counts, type breakdown, coverage, latest run |
| POST | `/api/projects/{id}/sources` | Save pasted requirements |
| POST | `/api/projects/{id}/sources/upload` | Upload `.txt`, `.md`, or `.csv` |
| GET | `/api/projects/{id}/sources` | List sources |
| POST | `/api/projects/{id}/analyze` | Run the heuristic analysis |
| GET | `/api/projects/{id}/analyses` | Analysis history |
| POST | `/api/projects/{id}/generate` | Generate and store test cases |
| GET | `/api/projects/{id}/test-cases` | Search, filter, sort, paginate |
| GET, PATCH, DELETE | `/api/test-cases/{id}` | Read, edit, or delete one case |
| POST | `/api/projects/{id}/test-cases/bulk` | Delete, update, or assign a suite |
| GET | `/api/projects/{id}/duplicates` | Title-similarity groups |
| GET | `/api/projects/{id}/coverage` | Acceptance-criteria mapping |
| GET, POST | `/api/projects/{id}/suites` | List or create suites |
| PATCH, DELETE | `/api/suites/{id}` | Rename or delete a suite |
| POST | `/api/projects/{id}/exports` | Download `xlsx`, `csv`, or `json` |

## Generate body

```json
{
  "source_id": "uuid",
  "analysis_id": "uuid",
  "types": ["functional", "negative", "boundary"],
  "suite_name": "Sprint 12"
}
```

`analysis_id` is optional. When it is omitted, the latest analysis for the source is used, or a new one is created.

## Settings body

```json
{
  "provider": "mock",
  "model": "",
  "temperature": 0.2,
  "max_tokens": 4000
}
```

Extra fields, including any key field, are rejected. The response reports whether each remote provider is configured. It does not include the key.

## Errors

- `422` for invalid input, an unsupported sort field, or provider output that is still invalid after one repair attempt.
- `415` for an upload that is not `.txt`, `.md`, or `.csv`.
- `413` when an upload exceeds the size limit.
- `400` when a remote provider is selected and its key is missing.
- `502` when a remote provider returns an HTTP error. The response body from that provider is not forwarded.
