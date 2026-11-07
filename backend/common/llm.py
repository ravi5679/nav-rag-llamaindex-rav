"""Step 2 for every RAG type: configure LlamaIndex's LLM + embedding model once, on import."""
from common.config import OPENAI_API_KEY, get_config
from rag_steps.llamaindex_settings import configure_llamaindex_settings

configure_llamaindex_settings(
    api_key=OPENAI_API_KEY,
    llm_model=get_config("llm.model"),
    temperature=get_config("llm.temperature"),
    embedding_model=get_config("embeddings.model"),
)
