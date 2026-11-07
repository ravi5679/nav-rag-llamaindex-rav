"""Ingest step - Chunk: split Documents into smaller pieces with SentenceSplitter."""
import logging

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode

logger = logging.getLogger(__name__)


def chunk_documents(documents: list[Document], chunk_size: int, chunk_overlap: int) -> list[BaseNode]:
    """Split each Document into chunks ("nodes") of at most `chunk_size` tokens.

    Why chunk at all:
      - the LLM prompt has limited space, so we can only send a few pieces of text
      - small, focused chunks match a question better than a whole page

    SentenceSplitter tries to break at sentence boundaries instead of mid-sentence, and
    `chunk_overlap` repeats a few tokens between neighbouring chunks so context isn't lost
    at the edges. Each chunk keeps its document's metadata (file_name, page_label, ...).
    """
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.get_nodes_from_documents(documents)
    logger.info("Chunked %d documents into %d chunks (size %d, overlap %d)",
                len(documents), len(chunks), chunk_size, chunk_overlap)
    return chunks
