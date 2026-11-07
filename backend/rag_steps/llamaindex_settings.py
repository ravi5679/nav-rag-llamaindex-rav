"""Step 2 - LlamaIndex Settings configuration (LLM + embedding model)."""
import logging

from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

logger = logging.getLogger(__name__)


def configure_llamaindex_settings(api_key: str, llm_model: str, temperature: float, embedding_model: str) -> None:
    """Set LlamaIndex's global LLM and embedding model. The embed, index, retriever and
    query-engine steps all pick these up automatically, so we configure them once here.

    Chunking is NOT set here on purpose: it's an explicit step (chunk_documents.py) so you can see it.
    """
    # LLM: writes the final answer from the retrieved chunks
    Settings.llm = OpenAI(model=llm_model, temperature=temperature, api_key=api_key)
    logger.info("LLM configured: %s (temperature: %s)", llm_model, temperature)

    # Embedding model: turns text into vectors. Documents and questions MUST use the
    # same model, otherwise their vectors can't be compared.
    Settings.embed_model = OpenAIEmbedding(model=embedding_model, api_key=api_key)
    logger.info("Embedding model configured: %s", embedding_model)
