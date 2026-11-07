"""Hybrid RAG endpoints: POST /api/v1/hybrid/query, /ingest, /reindex."""
from common.rag_routes import create_rag_router
from hybrid_rag import pipeline

router = create_rag_router(pipeline.RAG, pipeline.query)
