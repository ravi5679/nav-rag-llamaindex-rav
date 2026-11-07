"""Ingestion + index storage shared by every RAG type (naive, hybrid, ...).

Ingest is the same for all of them:  Upload -> Chunk -> Embedding -> Vector DB + indexing.
What differs is only how they RETRIEVE, which lives in naive_rag/ and hybrid_rag/.

Each (session, RAG type) has its own file + LanceDB + saved index (see session.py).
"""
import logging
import shutil
import threading
from collections import defaultdict

from fastapi import UploadFile
from llama_index.core import VectorStoreIndex

import common.llm  # noqa: F401  (Step 2: configures the LLM + embedding model)
from common.config import get_config
from common.session import delete_session_files, find_expired_sessions, rag_paths
from common.utils import save_upload
from rag_steps.chunk_documents import chunk_documents
from rag_steps.embed_chunks import embed_chunks
from rag_steps.load_documents import load_documents
from rag_steps.vector_index import clear_index_storage, create_vector_index, index_is_saved, load_vector_index
from rag_steps.vector_store import clear_vector_store, create_vector_store, vector_store_has_data

logger = logging.getLogger(__name__)

CHUNK_SIZE = get_config("embeddings.chunk_size")
CHUNK_OVERLAP = get_config("embeddings.chunk_overlap")
TABLE_NAME = get_config("vector_store.table_name")

# Loaded indexes, keyed by (session_id, rag), so questions don't re-read them from disk
_indexes: dict[tuple[str, str], VectorStoreIndex] = {}
# One lock per (session, rag): an upload, a reindex and a cleanup never overlap
_locks: defaultdict[tuple[str, str], threading.Lock] = defaultdict(threading.Lock)


def _clear_index(session_id: str, rag: str) -> None:
    paths = rag_paths(session_id, rag)
    _indexes.pop((session_id, rag), None)
    clear_vector_store(paths.vector_db_path, TABLE_NAME)
    clear_index_storage(paths.index_path)


def _build_index(session_id: str, rag: str) -> int:
    """Upload (read) -> Chunk -> Embedding -> Vector DB + indexing for the saved file."""
    paths = rag_paths(session_id, rag)
    documents = load_documents(str(paths.data_dir))                 # Upload: read the saved file
    if not documents:
        return 0
    chunks = chunk_documents(documents, CHUNK_SIZE, CHUNK_OVERLAP)  # Chunk (SentenceSplitter)
    chunks = embed_chunks(chunks)                                   # Embedding (OpenAI)
    vector_store = create_vector_store(paths.vector_db_path, TABLE_NAME)
    _indexes[(session_id, rag)] = create_vector_index(chunks, vector_store, paths.index_path)  # Vector DB + index
    return len(documents)


# ---------- used by the RAG routes ----------

def replace_document(session_id: str, rag: str, file: UploadFile) -> tuple[str, int]:
    """One file per session and RAG type: delete the previous one + its index, ingest the new one."""
    with _locks[(session_id, rag)]:
        paths = rag_paths(session_id, rag)
        _clear_index(session_id, rag)
        shutil.rmtree(paths.data_dir, ignore_errors=True)
        dest = save_upload(file, paths.data_dir)
        count = _build_index(session_id, rag)
    logger.info("[%s] session %s: ingested %s (%d documents)", rag, session_id[:8], dest.name, count)
    return dest.name, count


def rebuild_index(session_id: str, rag: str) -> int:
    """Rebuild the index from the current file."""
    with _locks[(session_id, rag)]:
        _clear_index(session_id, rag)
        return _build_index(session_id, rag)


def index_exists(session_id: str, rag: str) -> bool:
    """The vector DB and the saved index must both exist; they're always written together."""
    paths = rag_paths(session_id, rag)
    return vector_store_has_data(paths.vector_db_path, TABLE_NAME) and index_is_saved(paths.index_path)


def get_index(session_id: str, rag: str) -> VectorStoreIndex:
    """The session's index for this RAG type (loaded from disk once, then kept in memory)."""
    if not index_exists(session_id, rag):
        raise RuntimeError("Index is empty. Ingest documents first.")
    index = _indexes.get((session_id, rag))
    if index is None:
        paths = rag_paths(session_id, rag)
        index = load_vector_index(create_vector_store(paths.vector_db_path, TABLE_NAME), paths.index_path)
        _indexes[(session_id, rag)] = index
    return index


# ---------- deleting sessions (logout + cleanup job) ----------

def delete_session(session_id: str) -> None:
    """Delete everything of a session, for every RAG type: files, embeddings, indexes, memory."""
    keys = {k for k in [*_locks, *_indexes] if k[0] == session_id}
    for key in keys:
        with _locks[key]:
            _indexes.pop(key, None)
    delete_session_files(session_id)
    for key in keys:
        _locks.pop(key, None)


def cleanup_expired_sessions() -> int:
    """Delete every idle/old session. Returns how many were deleted."""
    expired = find_expired_sessions()
    for session_id in expired:
        delete_session(session_id)
        logger.info("Session %s expired: files, embeddings and indexes deleted", session_id[:8])
    return len(expired)
