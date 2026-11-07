# Backend API (FastAPI + LlamaIndex + LanceDB)

Two RAG techniques behind one API, with accounts and private, auto-deleted sessions:

- **Naive RAG** (`naive_rag/`): vector search only
- **Hybrid RAG** (`hybrid_rag/`): vector search + BM25 keyword search, merged with Reciprocal Rank Fusion

Ingestion is identical for both; only retrieval differs.

## Run

```powershell
cd backend
uv run uvicorn main:app --reload --port 8000   # docs at http://localhost:8000/docs
uv run pytest
```

## Structure

```
backend/
├── main.py                 FastAPI app: wires auth + both RAG routers, health, cleanup job
├── rag_steps/              One file per step; take everything as arguments (no app config)
│   ├── llamaindex_settings.py   Setup: LLM + embedding model (LlamaIndex Settings)
│   ├── vector_store.py          Setup: create / check / clear the LanceDB vector store
│   ├── load_documents.py        Ingest 1 - Upload: files -> Documents
│   ├── chunk_documents.py       Ingest 2 - Chunk: SentenceSplitter
│   ├── embed_chunks.py          Ingest 3 - Embedding: one vector per chunk
│   ├── vector_index.py          Ingest 4 - Vector DB + indexing: LanceDB + saved index
│   ├── query_engine.py          Query: vector retriever + RetrieverQueryEngine
│   └── hybrid_retriever.py      Query (hybrid): BM25 keyword retriever + QueryFusionRetriever (RRF)
├── naive_rag/
│   ├── pipeline.py         query(): vector search -> LLM
│   └── routes.py           /api/v1/naive/query | ingest | reindex
├── hybrid_rag/
│   ├── pipeline.py         query(): vector + keyword search -> fusion -> LLM
│   └── routes.py           /api/v1/hybrid/query | ingest | reindex
├── common/                 Shared by every RAG type
│   ├── config.py           Step 1: CONFIG dict + get_config("llm.model"), values from .env
│   ├── llm.py              Step 2: configures LlamaIndex once
│   ├── index_store.py      Ingestion + per-session index storage, session deletion/cleanup
│   ├── rag_routes.py       create_rag_router(): the 3 endpoints every RAG type exposes
│   ├── auth.py             Accounts (SQLite + scrypt), login tokens, server-issued session ids
│   ├── auth_routes.py      /api/v1/auth/signup | login | me | logout
│   ├── session.py          Per-session + per-RAG folders, activity + expiry tracking
│   ├── schemas.py          Request/response models (the frontend depends on these)
│   ├── security.py         verify_api_key (X-API-Key header check)
│   └── utils.py            Save an upload, format sources
├── stamp_verification/     pdf_to_images · detect · features · references · match · pipeline · routes
├── stamps/                 Reference stamp images (synthetic samples for now)
├── stamp_samples/          Sample PDFs to try the stamp API / UI
├── tests/                  test_api, test_auth, test_sessions, test_stamps (+ fixtures/); use a temp folder
├── storage/users.db                       Accounts + active logins (password hashes only)
├── data/sessions/<id>/<rag>/              The uploaded file (one per RAG type)
└── storage/sessions/<id>/
    ├── naive/ and hybrid/
    │   ├── lancedb/                       Chunk text + vectors (+ full-text index for hybrid)
    │   └── index/                         Saved index: docstore (every chunk) + metadata
    └── session.json                       created_at / last_active timestamps
```

## Endpoints (used by the frontend)

| Method | Path | Body | Response |
|---|---|---|---|
| GET  | `/api/v1/health` | – | `{status, index_loaded: {naive, hybrid}}` |
| POST | `/api/v1/<rag>/query` | `{question, top_k?}` | `{answer, sources: [{file_name, score, text}]}` |
| POST | `/api/v1/<rag>/ingest` | form-data `file` | `{message, documents_added}` |
| POST | `/api/v1/<rag>/reindex` | – | `{message, documents_added}` |
| POST | `/api/v1/auth/signup` | `{email, password}` | `{token, session_id, user: {email}}` (201) |
| POST | `/api/v1/auth/login` | `{email, password}` | `{token, session_id, user: {email}}` |
| GET  | `/api/v1/auth/me` | – | `{email}` |
| POST | `/api/v1/auth/logout` | – | 204, session data deleted |

`<rag>` is `naive` or `hybrid`. All except `/health` need the `X-API-Key` header when `API_KEY` is set;
the RAG endpoints also need `Authorization: Bearer <token>` and the matching `X-Session-Id`.
Hybrid sources carry fused RRF scores (small numbers like 0.03), not similarities.

## Hybrid RAG settings (.env, optional)

- `HYBRID_VECTOR_TOP_K` (5): candidates from vector search
- `HYBRID_KEYWORD_TOP_K` (5): candidates from BM25 keyword search (LanceDB full-text search)
- `SIMILARITY_TOP_K` (4): chunks sent to the LLM after fusion (also used by Naive RAG)

## Accounts and login

- Signup / login return `{token, session_id, user}`. Every login gets a fresh, empty session.
- The backend rejects a session id that doesn't belong to the token. A login lasts as long as its session.
- Logout ends the login **and deletes the session's files, embeddings and indexes for every RAG type**.

## Sessions and automatic cleanup

- Each session only sees its own documents; Naive and Hybrid each keep their own file and index.
- **One file per RAG type:** uploading a new file deletes the previous file, its embeddings and its index first.
- **Automatic deletion:** a background job inside the app runs every `SESSION_CLEANUP_INTERVAL_MINUTES` (5)
  and deletes sessions idle for `SESSION_IDLE_MINUTES` (60) or older than `SESSION_MAX_HOURS` (24).
  Expired sessions are also removed at startup.
- Not covered: LangSmith traces (turn off `LANGSMITH_TRACING` for full deletion) and OpenAI's own retention.

## Stamp verification (`stamp_verification/`)

`POST /api/v1/stamps/verify` (form-data `file`, a PDF; logged-in users) finds official stamps and matches
them against the reference images in `backend/stamps/` (file name = stamp id). `GET /api/v1/stamps/references`
lists the references. Classical computer vision, no AI model or GPU:

1. **Render** every page at 200 DPI (PyMuPDF)
2. **Detect**: keep coloured-ink pixels (HSV saturation, so black text drops out), merge strokes (morphology),
   keep blobs that are stamp-sized and round/rectangular (OpenCV contours). Round black seals via a fallback.
3. **Match**: SIFT keypoints + ratio test + RANSAC homography against each reference, then warp the stamp
   onto the reference and measure ink overlap. `confidence = 0.7 × keypoint score + 0.3 × overlap`
4. **Verify**: `Matched` if confidence ≥ `STAMP_MATCH_THRESHOLD` (0.55) and ≥ `STAMP_MATCH_MARGIN` (0.10)
   ahead of the 2nd-best reference; otherwise `Unknown Stamp`. Nothing detected: `No Stamp`.

Response: file name, `stamp_present` (Yes/No), final `status`, best `matched_reference` + `confidence`, and
per stamp: page, box, extracted image (PNG data URI), matched reference, confidence, top 3 candidates.

The references in `backend/stamps/` are **synthetic samples** (`scripts/make_stamp_samples.py`); replace them
with real reference stamps (one clean image each, ink on white). Changes are picked up without a restart.
Measure accuracy on your own documents with `scripts/evaluate_stamps.py` and tune the two thresholds.

Settings (.env, optional): `STAMP_REFERENCES_DIR`, `STAMP_MATCH_THRESHOLD`, `STAMP_MATCH_MARGIN`,
`STAMP_RENDER_DPI`, `STAMP_MAX_PAGES` (20), `STAMP_MAX_FILE_MB` (20).

## Adding another RAG type

1. Write its retrieval in `rag_steps/` (reuse the ingest steps as they are).
2. Create `<name>_rag/pipeline.py` with `RAG = "<name>"` and an async `query(session_id, question, top_k)`.
3. Create `<name>_rag/routes.py`: `router = create_rag_router(pipeline.RAG, pipeline.query)`.
4. Include the router in `main.py` and add the name to `RAG_TYPES`.
