"""Hybrid RAG query step - keyword (BM25) search + vector search, merged with rank fusion.

Why hybrid: vector search understands meaning ("car" ~ "vehicle") but can miss exact terms
such as codes, names or IDs ("INV-7731"). Keyword search finds exact terms but not synonyms.
Running both and merging the rankings gets the strengths of each.
"""
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import QueryFusionRetriever, VectorIndexRetriever

from rag_steps.query_engine import create_vector_retriever


def create_keyword_retriever(index: VectorStoreIndex, similarity_top_k: int) -> VectorIndexRetriever:
    """Keyword search: LanceDB's full-text search, which ranks chunks with BM25.

    Same LanceDB table as the vector search, only query_type="fts" (full-text search).
    LanceDB builds the full-text index on the chunk text automatically on first use.
    """
    return VectorIndexRetriever(
        index=index,
        similarity_top_k=similarity_top_k,
        vector_store_kwargs={"query_type": "fts"},
    )


def create_hybrid_retriever(
    index: VectorStoreIndex, similarity_top_k: int, vector_top_k: int, keyword_top_k: int
) -> QueryFusionRetriever:
    """Run vector + keyword search and merge the two ranked lists with Reciprocal Rank Fusion.

    RRF scores each chunk by 1 / (60 + rank) in every list and adds them up, so a chunk that ranks
    well in BOTH lists wins. Only ranks matter, which is why the two very different score scales
    (cosine similarity vs BM25) don't need to be normalised. The final top `similarity_top_k` go to the LLM.
    """
    return QueryFusionRetriever(
        [create_vector_retriever(index, vector_top_k), create_keyword_retriever(index, keyword_top_k)],
        mode="reciprocal_rerank",
        similarity_top_k=similarity_top_k,
        num_queries=1,      # 1 = use the question as-is (more would ask the LLM to rewrite it)
        use_async=True,     # run both searches at the same time
    )
