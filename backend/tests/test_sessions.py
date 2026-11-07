"""Session expiry and cleanup, using fake timestamps instead of waiting. No OpenAI calls."""
import json
import time
import uuid

from common import index_store, session


def make_session(created_ago: float, idle_for: float) -> str:
    """Create a session with a fake uploaded file for every RAG type and fake timestamps."""
    sid = str(uuid.uuid4())
    for rag in ("naive", "hybrid"):
        data_dir = session.rag_paths(sid, rag).data_dir
        data_dir.mkdir(parents=True)
        (data_dir / "doc.txt").write_text("hello")
    meta = session.meta_file(sid)
    meta.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    meta.write_text(json.dumps({"created_at": now - created_ago, "last_active": now - idle_for}))
    return sid


def exists(sid: str) -> bool:
    return (session.DATA_ROOT / sid).exists() or (session.STORAGE_ROOT / sid).exists()


def test_active_session_is_kept():
    sid = make_session(created_ago=600, idle_for=60)
    index_store.cleanup_expired_sessions()
    assert exists(sid)


def test_idle_session_is_deleted_for_every_rag_type():
    sid = make_session(created_ago=2 * 3600, idle_for=session.IDLE_SECONDS + 60)
    index_store.cleanup_expired_sessions()
    assert not exists(sid)


def test_too_old_session_is_deleted_even_if_active():
    sid = make_session(created_ago=session.MAX_AGE_SECONDS + 60, idle_for=10)
    index_store.cleanup_expired_sessions()
    assert not exists(sid)


def test_touch_keeps_session_alive():
    sid = make_session(created_ago=2 * 3600, idle_for=session.IDLE_SECONDS + 60)
    session.touch(sid)                       # user did something
    index_store.cleanup_expired_sessions()
    assert exists(sid)


def test_rag_types_have_separate_folders():
    sid = str(uuid.uuid4())
    naive, hybrid = session.rag_paths(sid, "naive"), session.rag_paths(sid, "hybrid")
    assert naive.data_dir != hybrid.data_dir and naive.vector_db_path != hybrid.vector_db_path
