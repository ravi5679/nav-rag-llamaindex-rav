"""Small helpers that aren't RAG steps themselves."""
import shutil
from pathlib import Path

from fastapi import UploadFile
from llama_index.core.schema import NodeWithScore


def save_upload(file: UploadFile, folder: Path) -> Path:
    """Save an uploaded file into `folder` and return its path."""
    folder.mkdir(parents=True, exist_ok=True)
    # Keep only the bare filename so "../../evil.py" can't escape the folder
    dest = folder / Path(file.filename).name
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)   # streams in pieces, not all into memory
    return dest


def format_sources(nodes: list[NodeWithScore], max_chars: int = 500) -> list[dict]:
    """Turn retrieved chunks into the `sources` list the frontend shows under each answer."""
    return [
        {
            "file_name": n.metadata.get("file_name"),
            "score": n.score,                       # higher = more similar to the question
            "text": n.get_content()[:max_chars],    # a preview, not the whole chunk
        }
        for n in nodes
    ]
