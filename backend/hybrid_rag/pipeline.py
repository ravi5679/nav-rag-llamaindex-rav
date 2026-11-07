"""Hybrid RAG: answer from chunks found by keyword search (BM25) AND vector search, merged by rank.

Ingest (shared, common/index_store.py):  Upload -> Chunk -> Embedding -> Vector DB + indexing
Query  (this file):                       vector search + keyword search -> fusion (RRF)
                                          -> prompt -> LLM answer + sources
"""
from langsmith import traceable

from common import index_store
from common.config import get_config
from common.utils import format_sources
from rag_steps.hybrid_retriever import create_hybrid_retriever
from rag_steps.query_engine import create_query_engine

RAG = "hybrid"


@traceable(name="hybrid_rag_query", run_type="chain")   # shows each query in LangSmith
async def query(session_id: str, question: str, top_k: int | None = None) -> dict:
    index = index_store.get_index(session_id, RAG)             # raises if nothing was uploaded
    top_k = top_k or get_config("index.similarity_top_k")

    retriever = create_hybrid_retriever(
        index,
        similarity_top_k=top_k,                                # chunks sent to the LLM
        # each search returns at least top_k candidates, so fusion has enough to choose from
        vector_top_k=max(top_k, get_config("hybrid.vector_top_k")),
        keyword_top_k=max(top_k, get_config("hybrid.keyword_top_k")),
    )
    response = await create_query_engine(retriever).aquery(question)
    return {"answer": str(response), "sources": format_sources(response.source_nodes)}
