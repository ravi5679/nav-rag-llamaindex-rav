"""Checks the RAG endpoints the frontend relies on, for every RAG type. No OpenAI calls."""
import uuid

import pytest
from fastapi.testclient import TestClient

from common.config import API_KEY
from main import RAG_TYPES, app


@pytest.fixture
def client():
    # `with` runs the lifespan (user tables, startup cleanup, background job)
    with TestClient(app) as c:
        if API_KEY:
            c.headers["X-API-Key"] = API_KEY
        res = c.post("/api/v1/auth/signup", json={"email": f"{uuid.uuid4().hex}@test.dev", "password": "secret-123"})
        body = res.json()
        c.headers["Authorization"] = f"Bearer {body['token']}"
        c.headers["X-Session-Id"] = body["session_id"]
        yield c


def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "index_loaded": {"naive": False, "hybrid": False}}


@pytest.mark.parametrize("rag", RAG_TYPES)
def test_query_before_upload_says_index_empty(client, rag):
    res = client.post(f"/api/v1/{rag}/query", json={"question": "hello?"})
    assert res.status_code == 400
    assert res.json()["detail"] == "Index is empty. Ingest documents first."


@pytest.mark.parametrize("rag", RAG_TYPES)
def test_rag_endpoints_need_login(client, rag):
    del client.headers["Authorization"]
    assert client.post(f"/api/v1/{rag}/query", json={"question": "hello?"}).status_code == 401
    assert client.post(f"/api/v1/{rag}/reindex").status_code == 401


@pytest.mark.parametrize("session_header", [None, str(uuid.uuid4()), "../../etc"])
@pytest.mark.parametrize("rag", RAG_TYPES)
def test_session_must_match_login(client, rag, session_header):
    del client.headers["X-Session-Id"]
    headers = {"X-Session-Id": session_header} if session_header else {}
    res = client.post(f"/api/v1/{rag}/query", json={"question": "hello?"}, headers=headers)
    assert res.status_code == 401


@pytest.mark.parametrize("rag", RAG_TYPES)
def test_query_rejects_short_question(client, rag):
    assert client.post(f"/api/v1/{rag}/query", json={"question": "hi"}).status_code == 422


@pytest.mark.parametrize("rag", RAG_TYPES)
def test_ingest_rejects_unsupported_type(client, rag):
    res = client.post(f"/api/v1/{rag}/ingest", files={"file": ("evil.exe", b"x")})
    assert res.status_code == 400


def test_old_unprefixed_paths_are_gone(client):
    assert client.post("/api/v1/query", json={"question": "hello?"}).status_code == 404


def test_wrong_api_key_is_rejected(client):
    if not API_KEY:
        pytest.skip("API_KEY not set")
    res = client.post("/api/v1/naive/query", json={"question": "hello?"}, headers={"X-API-Key": "wrong"})
    assert res.status_code == 401
