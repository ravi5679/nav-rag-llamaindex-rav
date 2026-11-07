"""Step 4 - Document loading (PDF, TXT, MD, DOCX, CSV)."""
import logging
from pathlib import Path

from llama_index.core import Document, SimpleDirectoryReader

logger = logging.getLogger(__name__)


def load_documents(folder: str, files: list[Path] | None = None) -> list[Document]:
    """Read files into LlamaIndex Documents (text + metadata such as file_name, page_label).

    - files=None  -> load every file in `folder` (used for a full rebuild)
    - files=[...] -> load only those files (used when one file is uploaded)

    SimpleDirectoryReader picks the right parser per file type; a PDF becomes one Document per page.
    """
    if files:
        reader = SimpleDirectoryReader(input_files=[str(f) for f in files])
    else:
        folder_path = Path(folder)
        if not folder_path.exists() or not any(folder_path.iterdir()):
            logger.warning("No documents found in %s", folder)
            return []
        reader = SimpleDirectoryReader(folder, recursive=True)

    documents = reader.load_data()
    logger.info("Loaded %d documents", len(documents))
    return documents
