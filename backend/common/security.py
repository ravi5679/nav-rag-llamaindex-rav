"""API key check, used as a FastAPI dependency on protected endpoints."""
import secrets

from fastapi import Header, HTTPException

from common.config import API_KEY


async def verify_api_key(x_api_key: str | None = Header(default=None)):
    """Reject requests without the right X-API-Key header (skipped if API_KEY isn't set)."""
    # compare_digest takes the same time whether the first or last character is wrong,
    # so an attacker can't guess the key by measuring response times
    if API_KEY and not secrets.compare_digest(x_api_key or "", API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")
