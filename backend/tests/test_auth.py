"""Sign up, log in, log out and session expiry. No OpenAI calls."""
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from common import session
from common.config import API_KEY
from main import app

PASSWORD = "secret-123"


@pytest.fixture
def client():
    with TestClient(app) as c:
        if API_KEY:
            c.headers["X-API-Key"] = API_KEY
        yield c


def new_email() -> str:
    return f"{uuid.uuid4().hex[:10]}@test.dev"


def auth_headers(body: dict) -> dict:
    return {"Authorization": f"Bearer {body['token']}", "X-Session-Id": body["session_id"]}


def test_signup_returns_token_and_session(client):
    email = new_email()
    res = client.post("/api/v1/auth/signup", json={"email": email.upper(), "password": PASSWORD})
    assert res.status_code == 201
    body = res.json()
    assert body["user"] == {"email": email}           # stored lower-case
    assert body["token"] and uuid.UUID(body["session_id"])


def test_duplicate_email_is_rejected(client):
    email = new_email()
    client.post("/api/v1/auth/signup", json={"email": email, "password": PASSWORD})
    res = client.post("/api/v1/auth/signup", json={"email": email, "password": PASSWORD})
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


@pytest.mark.parametrize("email,password", [("not-an-email", PASSWORD), (new_email(), "short")])
def test_signup_validates_input(client, email, password):
    assert client.post("/api/v1/auth/signup", json={"email": email, "password": password}).status_code == 400


def test_login_and_me(client):
    email = new_email()
    client.post("/api/v1/auth/signup", json={"email": email, "password": PASSWORD})
    res = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200
    me = client.get("/api/v1/auth/me", headers=auth_headers(res.json()))
    assert me.json() == {"email": email}


@pytest.mark.parametrize("which", ["password", "email"])
def test_wrong_credentials_get_the_same_error(client, which):
    email = new_email()
    client.post("/api/v1/auth/signup", json={"email": email, "password": PASSWORD})
    creds = {"email": email, "password": "wrong-pass"} if which == "password" else {"email": new_email(), "password": PASSWORD}
    res = client.post("/api/v1/auth/login", json=creds)
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password."


def test_each_login_gets_its_own_session(client):
    email = new_email()
    a = client.post("/api/v1/auth/signup", json={"email": email, "password": PASSWORD}).json()
    b = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}).json()
    assert a["session_id"] != b["session_id"]
    # login A can't use login B's session
    headers = {"Authorization": f"Bearer {a['token']}", "X-Session-Id": b["session_id"]}
    assert client.post("/api/v1/naive/reindex", headers=headers).status_code == 401


def test_logout_ends_login_and_deletes_session_data(client):
    body = client.post("/api/v1/auth/signup", json={"email": new_email(), "password": PASSWORD}).json()
    sid = body["session_id"]
    for rag in ("naive", "hybrid"):                         # pretend a file was uploaded to each RAG
        data_dir = session.rag_paths(sid, rag).data_dir
        data_dir.mkdir(parents=True)
        (data_dir / "doc.txt").write_text("hello")

    assert client.post("/api/v1/auth/logout", headers=auth_headers(body)).status_code == 204
    assert not (session.DATA_ROOT / sid).exists() and not session.meta_file(sid).exists()
    assert client.get("/api/v1/auth/me", headers=auth_headers(body)).status_code == 401


def test_expired_session_logs_the_user_out(client):
    body = client.post("/api/v1/auth/signup", json={"email": new_email(), "password": PASSWORD}).json()
    meta_file = session.meta_file(body["session_id"])
    meta = json.loads(meta_file.read_text())
    meta["last_active"] -= session.IDLE_SECONDS + 60       # pretend the user went idle
    meta_file.write_text(json.dumps(meta))

    res = client.post("/api/v1/hybrid/reindex", headers=auth_headers(body))
    assert res.status_code == 401
    assert "expired" in res.json()["detail"]
