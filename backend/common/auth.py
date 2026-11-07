"""User accounts and login, using only the Python standard library.

- Accounts live in SQLite (storage/users.db). Passwords are hashed with scrypt + a random salt.
- Login returns a random token (the browser sends it as "Authorization: Bearer <token>") and a
  server-issued session id (sent as X-Session-Id). Only a SHA-256 hash of the token is stored.
- A login lasts as long as its RAG session: when the session expires (see session.py) or the
  user logs out, the token stops working.
"""
import hashlib
import hmac
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path

from fastapi import Header, HTTPException

from common.config import get_config
from common.session import is_expired, touch

DB_PATH = Path(get_config("auth.db_path"))
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
MIN_PASSWORD, MAX_PASSWORD = 8, 128


class AuthError(Exception):
    """Wrong credentials, duplicate account, invalid token, ..."""


# ---------- database ----------

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(_connect()) as conn, conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS logins (
                token_hash TEXT PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                session_id TEXT NOT NULL,
                created_at REAL NOT NULL
            );
        """)


# ---------- passwords ----------

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    _, salt_hex, digest_hex = stored.split("$")
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1, dklen=32)
    return hmac.compare_digest(digest.hex(), digest_hex)


# Used when the email doesn't exist, so a wrong email takes as long as a wrong password
_DUMMY_HASH = hash_password(secrets.token_hex(8))


# ---------- accounts + logins ----------

def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _start_login(conn: sqlite3.Connection, user_id: int) -> tuple[str, str]:
    """Create a token + a fresh RAG session for this user. Returns (token, session_id)."""
    token, session_id = secrets.token_urlsafe(32), str(uuid.uuid4())
    conn.execute(
        "INSERT INTO logins (token_hash, user_id, session_id, created_at) VALUES (?, ?, ?, ?)",
        (_token_hash(token), user_id, session_id, time.time()),
    )
    touch(session_id)   # the session starts now (otherwise it would count as expired)
    return token, session_id


def signup(email: str, password: str) -> tuple[str, str, str]:
    """Create an account and log it in. Returns (email, token, session_id)."""
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise AuthError("Enter a valid email address.")
    if not MIN_PASSWORD <= len(password) <= MAX_PASSWORD:
        raise AuthError(f"Password must be {MIN_PASSWORD}-{MAX_PASSWORD} characters.")
    with closing(_connect()) as conn, conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                (email, hash_password(password), time.time()),
            )
        except sqlite3.IntegrityError:
            raise AuthError("An account with this email already exists.")
        return (email, *_start_login(conn, cur.lastrowid))


def login(email: str, password: str) -> tuple[str, str, str]:
    """Check the credentials and start a new login. Returns (email, token, session_id)."""
    email = email.strip().lower()
    with closing(_connect()) as conn, conn:
        user = conn.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,)).fetchone()
        ok = verify_password(password[:MAX_PASSWORD], user["password_hash"] if user else _DUMMY_HASH)
        if not (user and ok):
            raise AuthError("Invalid email or password.")
        return (email, *_start_login(conn, user["id"]))


def authenticate(token: str) -> tuple[str, str]:
    """Token -> (email, session_id). Fails if the token is unknown or its session has expired."""
    with closing(_connect()) as conn, conn:
        row = conn.execute(
            "SELECT u.email, l.session_id FROM logins l JOIN users u ON u.id = l.user_id WHERE l.token_hash = ?",
            (_token_hash(token),),
        ).fetchone()
        if row is None:
            raise AuthError("Not logged in.")
        if is_expired(row["session_id"]):
            conn.execute("DELETE FROM logins WHERE token_hash = ?", (_token_hash(token),))
            raise AuthError("Your session has expired. Please log in again.")
        return row["email"], row["session_id"]


def logout(token: str) -> str | None:
    """End the login. Returns its session id (so the caller can delete the session's data)."""
    with closing(_connect()) as conn, conn:
        row = conn.execute("SELECT session_id FROM logins WHERE token_hash = ?", (_token_hash(token),)).fetchone()
        conn.execute("DELETE FROM logins WHERE token_hash = ?", (_token_hash(token),))
        return row["session_id"] if row else None


def purge_expired_logins() -> int:
    """Remove logins whose session has expired (keeps the table small)."""
    with closing(_connect()) as conn, conn:
        rows = conn.execute("SELECT token_hash, session_id FROM logins").fetchall()
        expired = [(r["token_hash"],) for r in rows if is_expired(r["session_id"])]
        conn.executemany("DELETE FROM logins WHERE token_hash = ?", expired)
        return len(expired)


# ---------- FastAPI dependencies ----------

def _bearer(authorization: str | None) -> str:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Not logged in.")
    return token


async def get_token(authorization: str | None = Header(default=None)) -> str:
    return _bearer(authorization)


async def get_user_session(
    authorization: str | None = Header(default=None),
    x_session_id: str | None = Header(default=None),
) -> str:
    """Require a valid login whose session id matches X-Session-Id; returns the session id."""
    try:
        _email, session_id = authenticate(_bearer(authorization))
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    if (x_session_id or "").lower() != session_id:
        raise HTTPException(status_code=401, detail="Session does not belong to this login.")
    touch(session_id)   # every request keeps the session (and the login) alive
    return session_id
