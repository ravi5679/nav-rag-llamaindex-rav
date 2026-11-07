"""Query step - retriever + query engine (shared by Naive and Hybrid RAG)."""
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import BaseRetriever, VectorIndexRetriever


def create_vector_retriever(index: VectorStoreIndex, similarity_top_k: int) -> VectorIndexRetriever:
    """Semantic search: embeds the question and fetches the `similarity_top_k` closest chunks."""
    return VectorIndexRetriever(index=index, similarity_top_k=similarity_top_k)


def create_query_engine(retriever: BaseRetriever) -> RetrieverQueryEngine:
    """Question-answering engine around any retriever:

    1. the retriever finds the relevant chunks
    2. the response synthesizer puts those chunks + the question into a prompt for the LLM
       (Settings.llm), which answers from that context
    """
    return RetrieverQueryEngine.from_args(retriever=retriever)
