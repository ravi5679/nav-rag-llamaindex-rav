"""Stamp detection + matching, on PDFs built from the fixture stamps. No network calls."""
import io
import uuid
from pathlib import Path

import numpy as np
import pymupdf
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from common.config import API_KEY
from main import app
from stamp_verification.pipeline import verify_pdf

FIXTURES = Path(__file__).parent / "fixtures"


def stamp_png(path: Path, rotate: float = 0, opacity: float = 0.9) -> bytes:
    """Reference image (ink on white) -> transparent PNG, rotated and faded like a real stamp."""
    rgb = np.array(Image.open(path).convert("RGB"))
    ink = (255 - rgb.min(axis=2)).astype(np.float32)          # 0 on white paper
    alpha = np.clip(ink * 3 * opacity, 0, 255).astype(np.uint8)
    img = Image.fromarray(np.dstack([rgb, alpha]), "RGBA").rotate(rotate, expand=True, resample=Image.BICUBIC)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_pdf(stamp: Path | None = None, rotate: float = 0, pages: int = 1, stamp_page: int = 0) -> bytes:
    doc = pymupdf.open()
    for p in range(pages):
        page = doc.new_page(width=595, height=842)
        for i in range(30):
            page.insert_text((60, 80 + i * 22), f"Clause {i + 1}. The parties agree to the terms of this agreement.")
        if stamp and p == stamp_page:
            page.insert_image(pymupdf.Rect(330, 540, 520, 730), stream=stamp_png(stamp, rotate))
    return doc.tobytes()


# ---------- pipeline ----------

@pytest.mark.parametrize("name,rotate", [("finance_dept_seal", 0), ("legal_seal", 37), ("hr_received", -12),
                                         ("notary_public", 160), ("quality_passed", 90)])
def test_known_stamp_is_matched(name, rotate):
    r = verify_pdf(make_pdf(FIXTURES / "stamps" / f"{name}.png", rotate), "doc.pdf")
    assert r["stamp_present"] == "Yes"
    assert r["status"] == "Matched"
    assert r["matched_reference"] == name
    assert r["confidence"] >= 0.55
    stamp = r["stamps"][0]
    assert stamp["stamp_image"].startswith("data:image/png;base64,")
    assert stamp["top_candidates"][0]["reference"] == name


def test_stamp_on_a_later_page_is_found():
    r = verify_pdf(make_pdf(FIXTURES / "stamps" / "hr_received.png", pages=3, stamp_page=1), "doc.pdf")
    assert r["pages_checked"] == 3
    assert [s["page"] for s in r["stamps"]] == [2]


def test_stamp_not_in_references_is_unknown():
    r = verify_pdf(make_pdf(FIXTURES / "unknown_stamp.png", rotate=10), "doc.pdf")
    assert r["stamp_present"] == "Yes"
    assert r["status"] == "Unknown Stamp"
    assert r["matched_reference"] is None
    assert r["stamps"][0]["matched_reference"] is None


def test_document_without_stamp():
    r = verify_pdf(make_pdf(), "plain.pdf")
    assert r == {"file_name": "plain.pdf", "pages_checked": 1, "stamp_present": "No", "status": "No Stamp",
                 "matched_reference": None, "confidence": 0.0, "stamps": []}


# ---------- API ----------

@pytest.fixture
def client():
    with TestClient(app) as c:
        if API_KEY:
            c.headers["X-API-Key"] = API_KEY
        body = c.post("/api/v1/auth/signup", json={"email": f"{uuid.uuid4().hex}@test.dev", "password": "secret-123"}).json()
        c.headers["Authorization"] = f"Bearer {body['token']}"
        c.headers["X-Session-Id"] = body["session_id"]
        yield c


def test_verify_endpoint(client):
    pdf = make_pdf(FIXTURES / "stamps" / "legal_seal.png", rotate=20)
    res = client.post("/api/v1/stamps/verify", files={"file": ("contract.pdf", pdf, "application/pdf")})
    assert res.status_code == 200
    body = res.json()
    assert body["file_name"] == "contract.pdf"
    assert (body["status"], body["matched_reference"]) == ("Matched", "legal_seal")


def test_verify_needs_login(client):
    del client.headers["Authorization"]
    res = client.post("/api/v1/stamps/verify", files={"file": ("a.pdf", make_pdf(), "application/pdf")})
    assert res.status_code == 401


@pytest.mark.parametrize("name,content", [("notes.txt", b"hello"), ("broken.pdf", b"not really a pdf")])
def test_verify_rejects_non_pdfs(client, name, content):
    assert client.post("/api/v1/stamps/verify", files={"file": (name, content)}).status_code == 400


def test_references_endpoint(client):
    res = client.get("/api/v1/stamps/references")
    assert res.status_code == 200
    assert sorted(r["name"] for r in res.json()) == sorted(p.stem for p in (FIXTURES / "stamps").glob("*.png"))
