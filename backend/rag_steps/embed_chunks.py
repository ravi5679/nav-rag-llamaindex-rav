"""Ingest step - Embedding: turn each chunk into a vector."""
import logging

from llama_index.core import Settings
from llama_index.core.schema import BaseNode, MetadataMode

logger = logging.getLogger(__name__)


def embed_chunks(chunks: list[BaseNode]) -> list[BaseNode]:
    """Attach an embedding vector (a list of numbers) to every chunk.

    Chunks with similar meaning get vectors that are close together, which is what lets
    us find relevant chunks for a question later. Uses Settings.embed_model from step 2,
    sent to OpenAI in batches, so this is the step that costs money and time.

    The index step sees that chunks already have vectors and doesn't embed them again.
    """
    texts = [c.get_content(metadata_mode=MetadataMode.EMBED) for c in chunks]
    vectors = Settings.embed_model.get_text_embedding_batch(texts)
    for chunk, vector in zip(chunks, vectors):
        chunk.embedding = vector
    logger.info("Embedded %d chunks", len(chunks))
    return chunks
