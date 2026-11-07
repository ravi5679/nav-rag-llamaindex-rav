# RAG App

FastAPI + LlamaIndex backend and a React (Vite, TypeScript) frontend.

```
backend/    FastAPI API (uv project)      -> http://localhost:8000
frontend/   React UI (Vite)               -> http://localhost:5173
docker-compose.yml   Nginx (React build) + backend, one origin on :8080
```

## Local development

```powershell
# 1. backend  (needs backend/.env with OPENAI_API_KEY and API_KEY)
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# 2. frontend (second terminal)
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to `localhost:8000`, so no CORS setup is needed in dev.
`frontend/.env.development` has `VITE_API_KEY`, which must equal `API_KEY` in `backend/.env`.
It is visible in the browser, so use it for local work only.

Tests: `cd backend; uv run pytest`

## Docker (production-style)

```powershell
# root .env (not committed) so compose can read the key:
#   API_KEY=<same value as in backend/.env>
docker compose up --build
```

Open http://localhost:8080. Nginx serves the React build and forwards `/api/*` to the
backend, adding the `X-API-Key` header itself, so the key is never sent to the browser.
`backend/data` and `backend/storage` are mounted as volumes so the index survives restarts.

In prod mode (`ENVIRONMENT=prod`) the backend requires a strong `API_KEY`, and `/docs` is disabled.

## Notes

- `npm install` uses `legacy-peer-deps` (see `frontend/.npmrc`) to work around an npm 10 resolver bug.
- After changing PDF parsing or documents by hand, call `POST /api/v1/reindex` (Documents page).
