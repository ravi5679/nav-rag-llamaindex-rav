"""The 3 endpoints every RAG type exposes: /api/v1/<rag>/query, /ingest, /reindex.

Ingest and reindex are the same for every RAG type; only the query function differs.
"""
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from common import auth, index_store
from common.config import get_config
from common.schemas import IngestResponse, QueryRequest, QueryResponse
from common.security import verify_api_key

QueryFn = Callable[[str, str, int | None], Awaitable[dict]]


def create_rag_router(rag: str, query_fn: QueryFn) -> APIRouter:
    router = APIRouter(prefix=f"/{rag}", tags=[f"{rag} rag"], dependencies=[Depends(verify_api_key)])

    @router.post("/query", response_model=QueryResponse)
    async def query(body: QueryRequest, session_id: str = Depends(auth.get_user_session)):
        try:
            return await query_fn(session_id, body.question, body.top_k)
        except RuntimeError as e:          # e.g. nothing uploaded yet
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/ingest", response_model=IngestResponse)
    async def ingest(file: UploadFile = File(...), session_id: str = Depends(auth.get_user_session)):
        ext = Path(file.filename or "").suffix.lower()
        if ext not in get_config("documents.allowed_extensions"):
            raise HTTPException(400, f"Unsupported file type: {ext}")
        # Replaces this RAG type's previous file. Embedding is slow, blocking work: run it in a thread
        name, count = await run_in_threadpool(index_store.replace_document, session_id, rag, file)
        return IngestResponse(message=f"Ingested {name}", documents_added=count)

    @router.post("/reindex", response_model=IngestResponse)
    async def reindex(session_id: str = Depends(auth.get_user_session)):
        count = await run_in_threadpool(index_store.rebuild_index, session_id, rag)
        return IngestResponse(message="Index rebuilt", documents_added=count)

    return router
