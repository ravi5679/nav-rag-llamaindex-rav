"""Step 1 - Environment setup and configuration.

All settings live in one CONFIG dictionary and are read with get_config("llm.model").
Values come from .env when set, otherwise the defaults below are used.
Secrets (API keys) are kept OUT of CONFIG so printing it never leaks them.
"""
import json
import os

from dotenv import load_dotenv

# Load .env into os.environ (also lets the OpenAI and LangSmith SDKs find their keys)
load_dotenv(override=False)

# ---------- Secrets: only from the environment, never hard-coded ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
API_KEY = os.getenv("API_KEY", "")            # clients send it as the X-API-Key header; empty = no check


# ---------- Configuration parameters for the RAG system ----------
CONFIG = {
    "app": {
        "name": os.getenv("APP_NAME", "NAIVE_RAG_API"),
        "environment": os.getenv("ENVIRONMENT", "dev"),          # dev | staging | prod
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "cors_origins": json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:3000"]')),
    },
    "llm": {
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),          # OpenAI chat model that writes answers
        "temperature": float(os.getenv("TEMPERATURE", "0.1")),   # low = factual, high = creative
    },
    "embeddings": {
        "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),  # OpenAI embedding model
        "chunk_size": int(os.getenv("CHUNK_SIZE", "512")),        # tokens per chunk
        "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "50")),   # tokens shared by neighbouring chunks
    },
    # Every session gets its own folders (see session.py):
    #   <documents.folder>/<session_id>/          the uploaded file
    #   <sessions.storage_root>/<session_id>/lancedb   vector store
    #   <sessions.storage_root>/<session_id>/index     saved index
    "vector_store": {
        "type": "lancedb",
        "table_name": os.getenv("LANCEDB_TABLE", "documents"),
    },
    "index": {
        "similarity_top_k": int(os.getenv("SIMILARITY_TOP_K", "4")),  # chunks sent to the LLM per question
    },
    "hybrid": {
        "vector_top_k": int(os.getenv("HYBRID_VECTOR_TOP_K", "5")),    # candidates from vector search
        "keyword_top_k": int(os.getenv("HYBRID_KEYWORD_TOP_K", "5")),  # candidates from BM25 keyword search
    },
    "documents": {
        "folder": os.path.join(os.getenv("DATA_DIR", "data"), "sessions"),
        "allowed_extensions": [".pdf", ".txt", ".md", ".docx", ".csv"],
    },
    "sessions": {
        "storage_root": os.path.join(os.getenv("STORAGE_DIR", "storage"), "sessions"),
        "idle_minutes": int(os.getenv("SESSION_IDLE_MINUTES", "60")),        # delete after this long unused
        "max_hours": int(os.getenv("SESSION_MAX_HOURS", "24")),              # delete this long after creation
        "cleanup_interval_minutes": int(os.getenv("SESSION_CLEANUP_INTERVAL_MINUTES", "5")),
    },
    "stamps": {
        "references_dir": os.getenv("STAMP_REFERENCES_DIR", "stamps"),           # one image per reference stamp
        "match_threshold": float(os.getenv("STAMP_MATCH_THRESHOLD", "0.55")),  # min confidence for "Matched"
        "match_margin": float(os.getenv("STAMP_MATCH_MARGIN", "0.10")),        # best must beat 2nd-best by this
        "render_dpi": int(os.getenv("STAMP_RENDER_DPI", "200")),
        "max_pages": int(os.getenv("STAMP_MAX_PAGES", "20")),
        "max_file_mb": int(os.getenv("STAMP_MAX_FILE_MB", "20")),
    },
    "auth": {
        "db_path": os.path.join(os.getenv("STORAGE_DIR", "storage"), "users.db"),   # SQLite: accounts + logins
    },
}


def get_config(key_path: str, default_value=None):
    """Get a configuration value using dot notation, e.g. get_config("llm.model")."""
    value = CONFIG
    for key in key_path.split("."):
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default_value
    return value


def is_prod() -> bool:
    return get_config("app.environment") == "prod"


def validate_config() -> None:
    """Fail fast at startup instead of with a confusing error on the first request."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set (add it to .env)")
    if get_config("embeddings.chunk_overlap") >= get_config("embeddings.chunk_size"):
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
    if is_prod():
        if not API_KEY or API_KEY == "change-me":
            raise ValueError("API_KEY must be set to a strong value in production")
        if "*" in get_config("app.cors_origins"):
            raise ValueError("Wildcard CORS is not allowed in production")


validate_config()
