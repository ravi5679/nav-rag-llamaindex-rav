"""Step 3 - Vector store setup (LanceDB).

LanceDB is a vector database that lives in a folder on disk: no server to run.
It stores each chunk's text, metadata and embedding vector, and finds the nearest vectors fast.
"""
import logging
from pathlib import Path

import lancedb
from llama_index.vector_stores.lancedb import LanceDBVectorStore

logger = logging.getLogger(__name__)


def create_vector_store(path: str, table_name: str) -> LanceDBVectorStore:
    """Connect to LanceDB at `path`. The table is created automatically when data is first added."""
    Path(path).mkdir(parents=True, exist_ok=True)
    vector_store = LanceDBVectorStore(uri=path, table_name=table_name)
    logger.debug("LanceDB vector store ready at %s (table: %s)", path, table_name)
    return vector_store


def vector_store_has_data(path: str, table_name: str) -> bool:
    """True if the table exists and holds at least one chunk."""
    db = lancedb.connect(path)
    if table_name not in db.list_tables().tables:
        return False
    return db.open_table(table_name).count_rows() > 0


def clear_vector_store(path: str, table_name: str) -> None:
    """Delete the table, e.g. before rebuilding the index from scratch."""
    db = lancedb.connect(path)
    if table_name in db.list_tables().tables:
        db.drop_table(table_name)
        logger.info("Dropped LanceDB table %s", table_name)
