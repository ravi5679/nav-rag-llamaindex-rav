"""Ingest step - Vector DB + indexing: store embedded chunks in LanceDB and save the index.

Two places on disk work together:
  - vector_store.path   (LanceDB)  chunk text + metadata + vectors, used for similarity search
  - index.storage_path  (JSON)     the index itself: docstore (every chunk) + index metadata
"""
import logging
import shutil
from pathlib import Path

from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.schema import BaseNode
from llama_index.vector_stores.lancedb import LanceDBVectorStore

logger = logging.getLogger(__name__)


def create_vector_index(chunks: list[BaseNode], vector_store: LanceDBVectorStore, storage_path: str) -> VectorStoreIndex:
    """Build a new index from embedded chunks: writes vectors to LanceDB and saves the index to storage_path."""
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    # store_nodes_override=True: also keep every chunk in the docstore. LanceDB alone would be
    # enough to answer questions, but the docstore makes the saved index complete (and is what
    # keyword search such as BM25 needs later, e.g. for Hybrid RAG).
    index = VectorStoreIndex(nodes=chunks, storage_context=storage_context, store_nodes_override=True)
    storage_context.persist(persist_dir=storage_path)
    logger.info("Created index with %d chunks (saved to %s)", len(chunks), storage_path)
    return index


def add_to_vector_index(index: VectorStoreIndex, chunks: list[BaseNode], storage_path: str) -> None:
    """Add embedded chunks to an existing index (appends to LanceDB) and save the index again."""
    index.insert_nodes(chunks)
    index.storage_context.persist(persist_dir=storage_path)
    logger.info("Added %d chunks to the index", len(chunks))


def load_vector_index(vector_store: LanceDBVectorStore, storage_path: str) -> VectorStoreIndex:
    """Load the saved index from storage_path, connected to the LanceDB vectors (no re-embedding)."""
    storage_context = StorageContext.from_defaults(vector_store=vector_store, persist_dir=storage_path)
    return load_index_from_storage(storage_context, store_nodes_override=True)


def index_is_saved(storage_path: str) -> bool:
    return (Path(storage_path) / "index_store.json").exists()


def clear_index_storage(storage_path: str) -> None:
    """Delete the saved index (used before a full rebuild)."""
    shutil.rmtree(storage_path, ignore_errors=True)
