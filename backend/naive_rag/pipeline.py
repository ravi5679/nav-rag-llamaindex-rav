"""Naive RAG: answer from the chunks that are closest in MEANING to the question.

Ingest (shared, common/index_store.py):  Upload -> Chunk -> Embedding -> Vector DB + indexing
Query  (this file):                       vector search (top-k) -> prompt -> LLM answer + sources
"""
from langsmith import traceable

from common import index_store
from common.config import get_config
from common.utils import format_sources
from rag_steps.query_engine import create_query_engine, create_vector_retriever

RAG = "naive"


@traceable(name="naive_rag_query", run_type="chain")   # shows each query in LangSmith
async def query(session_id: str, question: str, top_k: int | None = None) -> dict:
    index = index_store.get_index(session_id, RAG)            # raises if nothing was uploaded
    top_k = top_k or get_config("index.similarity_top_k")

    retriever = create_vector_retriever(index, top_k)         # semantic search only
    response = await create_query_engine(retriever).aquery(question)
    return {"answer": str(response), "sources": format_sources(response.source_nodes)}
