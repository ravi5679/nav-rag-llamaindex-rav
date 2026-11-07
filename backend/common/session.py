"""Sessions: each login gets its own private files, embeddings and indexes.

The server creates the session id at login (auth.py); the browser sends it back as X-Session-Id.
Inside a session, every RAG type ("naive", "hybrid") has its own folder, so they never mix:

    data/sessions/<id>/<rag>/                 the uploaded file
    storage/sessions/<id>/<rag>/lancedb       vector store
    storage/sessions/<id>/<rag>/index         saved index
    storage/sessions/<id>/session.json        created_at / last_active (shared by all RAG types)

Every request marks the session as active; idle/old sessions are deleted by
index_store.cleanup_expired_sessions().
"""
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from common.config import get_config

DATA_ROOT = Path(get_config("documents.folder"))
STORAGE_ROOT = Path(get_config("sessions.storage_root"))
IDLE_SECONDS = get_config("sessions.idle_minutes") * 60
MAX_AGE_SECONDS = get_config("sessions.max_hours") * 3600


@dataclass(frozen=True)
class RagPaths:
    data_dir: Path         # the uploaded file
    vector_db_path: str    # LanceDB
    index_path: str        # saved index (docstore + metadata)


def rag_paths(session_id: str, rag: str) -> RagPaths:
    """Folders of one RAG type ("naive" / "hybrid") inside a session."""
    root = STORAGE_ROOT / session_id / rag
    return RagPaths(
        data_dir=DATA_ROOT / session_id / rag,
        vector_db_path=str(root / "lancedb"),
        index_path=str(root / "index"),
    )


def meta_file(session_id: str) -> Path:
    return STORAGE_ROOT / session_id / "session.json"


# ---------- activity tracking (stored on disk so it survives a restart) ----------

def touch(session_id: str) -> None:
    """Mark the session as used right now (creates it on first use)."""
    path = meta_file(session_id)
    now = time.time()
    meta = _read_meta(path) or {"created_at": now}
    meta["last_active"] = now
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta))


def _read_meta(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def is_expired(session_id: str, now: float | None = None) -> bool:
    now = now or time.time()
    meta = _read_meta(meta_file(session_id))
    if meta is None:
        # No timestamps (e.g. left over from a crash): use the newest folder time instead
        times = [p.stat().st_mtime for p in (DATA_ROOT / session_id, STORAGE_ROOT / session_id) if p.exists()]
        return not times or now - max(times) > IDLE_SECONDS
    return now - meta["last_active"] > IDLE_SECONDS or now - meta["created_at"] > MAX_AGE_SECONDS


def find_expired_sessions() -> list[str]:
    """Session ids (from both the data and storage folders) that should be deleted."""
    ids = {p.name for root in (DATA_ROOT, STORAGE_ROOT) if root.exists() for p in root.iterdir() if p.is_dir()}
    return sorted(i for i in ids if is_expired(i))


def delete_session_files(session_id: str) -> None:
    """Remove everything of the session, for every RAG type: files, embeddings, indexes, timestamps."""
    shutil.rmtree(DATA_ROOT / session_id, ignore_errors=True)
    shutil.rmtree(STORAGE_ROOT / session_id, ignore_errors=True)
