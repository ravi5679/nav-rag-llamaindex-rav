"""The FastAPI app: wires together auth, Naive RAG and Hybrid RAG. No RAG logic here.

Run from the backend folder:  uv run uvicorn main:app --reload --port 8000

    /api/v1/health
    /api/v1/auth/...      common/auth_routes.py
    /api/v1/naive/...     naive_rag/   (vector search)
    /api/v1/hybrid/...    hybrid_rag/  (vector + keyword search, rank fusion)
    /api/v1/stamps/...    stamp_verification/  (detect + match official stamps in PDFs)
"""
import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from common import auth, auth_routes, index_store
from common.config import get_config, is_prod
from hybrid_rag.routes import router as hybrid_router
from naive_rag.routes import router as naive_router
from stamp_verification.routes import router as stamps_router

logging.basicConfig(level=get_config("app.log_level"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

RAG_TYPES = ["naive", "hybrid"]


# ---------- background cleanup ----------
def _cleanup() -> None:
    index_store.cleanup_expired_sessions()   # files + embeddings + indexes of idle/old sessions
    auth.purge_expired_logins()              # their logins stop working too


async def cleanup_loop():
    """Background job inside the app: delete idle/old sessions every few minutes."""
    interval = get_config("sessions.cleanup_interval_minutes") * 60
    while True:
        await asyncio.sleep(interval)
        try:
            await run_in_threadpool(_cleanup)
        except Exception:          # never let one failed run stop future cleanups
            logger.exception("Session cleanup failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create the user tables, remove sessions that expired while the server was down,
    # then start the cleanup job
    auth.init_db()
    await run_in_threadpool(_cleanup)
    task = asyncio.create_task(cleanup_loop())
    yield
    # Shutdown: stop the job
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


# ---------- app ----------
app = FastAPI(
    title=get_config("app.name"),
    version="1.0.0",
    docs_url=None if is_prod() else "/docs",
    redoc_url=None if is_prod() else "/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_config("app.cors_origins"),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(naive_router, prefix="/api/v1")
app.include_router(hybrid_router, prefix="/api/v1")
app.include_router(stamps_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["health"])
async def health(authorization: str | None = Header(default=None), x_session_id: str | None = Header(default=None)):
    # Whether each RAG type has a document is only known for a logged-in session
    try:
        session_id = await auth.get_user_session(authorization, x_session_id)
        loaded = {rag: index_store.index_exists(session_id, rag) for rag in RAG_TYPES}
    except HTTPException:
        loaded = {rag: False for rag in RAG_TYPES}
    return {"status": "ok", "index_loaded": loaded}
