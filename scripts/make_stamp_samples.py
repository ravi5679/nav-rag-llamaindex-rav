"""Generates SYNTHETIC stamps and sample PDFs for developing/testing stamp verification.

Run from the repo root (uses the backend's venv):
    uv run --directory backend python ../scripts/make_stamp_samples.py

Writes:
  backend/stamps/*.png                       reference stamps (file name = stamp id)
  backend/tests/fixtures/unknown_stamp.png   a stamp that is NOT in the references
  backend/stamp_samples/*.pdf                sample documents to try in the UI

Replace backend/stamps/ with your real reference stamps when you have them.
"""
import io
import math
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1] / "backend"
FONTS = Path("C:/Windows/Fonts")
BOLD = str(FONTS / "arialbd.ttf")
SIZE = 600   # reference image size in pixels

BLUE, RED, PURPLE, GREEN = (30, 60, 170), (190, 30, 40), (110, 40, 150), (20, 120, 60)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(BOLD, size)


def _curved_text(img: Image.Image, text: str, radius: float, size: int, color, start_deg: float = -90) -> None:
    """Write text clockwise around the centre, one rotated letter at a time."""
    cx = cy = img.width / 2
    font = _font(size)
    step = 360 / len(text)
    for i, ch in enumerate(text):
        angle = math.radians(start_deg + i * step)
        letter = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(letter)
        w = d.textlength(ch, font=font)
        d.text((size - w / 2, size / 2), ch, font=font, fill=color)
        letter = letter.rotate(-(start_deg + i * step + 90), resample=Image.BICUBIC)
        x, y = cx + radius * math.cos(angle) - size, cy + radius * math.sin(angle) - size
        img.alpha_composite(letter, (int(x), int(y)))


def round_seal(ring_text: str, center: list[str], color, star: bool = False) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = SIZE / 2
    d.ellipse((12, 12, SIZE - 12, SIZE - 12), outline=color, width=14)
    d.ellipse((150, 150, SIZE - 150, SIZE - 150), outline=color, width=8)
    _curved_text(img, ring_text, radius=225, size=46, color=color)
    d = ImageDraw.Draw(img)
    if star:
        pts = [(c + 90 * math.cos(math.radians(-90 + k * 36)) * (1 if k % 2 == 0 else 0.42),
                c + 90 * math.sin(math.radians(-90 + k * 36)) * (1 if k % 2 == 0 else 0.42)) for k in range(10)]
        d.polygon(pts, fill=color)
    else:
        font = _font(40)
        for i, line in enumerate(center):
            w = d.textlength(line, font=font)
            d.text((c - w / 2, c - 25 * len(center) + i * 50), line, font=font, fill=color)
    return img


def rect_stamp(lines: list[str], color) -> Image.Image:
    img = Image.new("RGBA", (SIZE, int(SIZE * 0.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((8, 8, img.width - 8, img.height - 8), outline=color, width=12)
    d.rectangle((30, 30, img.width - 30, img.height - 30), outline=color, width=4)
    sizes = [52, 70, 40][: len(lines)]
    y = 55
    for line, s in zip(lines, sizes):
        font = _font(s)
        w = d.textlength(line, font=font)
        d.text(((img.width - w) / 2, y), line, font=font, fill=color)
        y += s + 28
    return img


REFERENCES = {
    "finance_dept_seal": round_seal("FINANCE DEPARTMENT * ACME CORP * ", ["APPROVED", "2026"], BLUE),
    "legal_seal": round_seal("LEGAL & COMPLIANCE * ACME CORP * ", [], RED, star=True),
    "notary_public": round_seal("NOTARY PUBLIC * STATE OF NEVADA * ", ["OFFICIAL", "SEAL"], GREEN),
    "hr_received": rect_stamp(["HUMAN RESOURCES", "RECEIVED", "ACME CORPORATION"], PURPLE),
    "quality_passed": rect_stamp(["QUALITY CONTROL", "PASSED", "INSPECTOR No. 17"], RED),
}
UNKNOWN = round_seal("SHIPPING DEPT * GLOBEX LTD * ", ["DISPATCHED"], BLUE)


def on_white(stamp: Image.Image) -> Image.Image:
    """Reference images are stored like a scan: ink on a white background."""
    bg = Image.new("RGB", stamp.size, "white")
    bg.paste(stamp, mask=stamp.split()[3])
    return bg


# ---------- sample documents ----------
def make_pdf(path: Path, stamp: Image.Image | None, rotate: float = 0, scale: float = 0.33,
             opacity: float = 0.9, pos=(0.62, 0.70), page_count: int = 1, stamp_page: int = 0) -> None:
    """A text document with (optionally) one stamp placed on top, rotated/scaled/faded."""
    doc = pymupdf.open()
    for p in range(page_count):
        page = doc.new_page(width=595, height=842)   # A4 in points
        page.insert_text((60, 70), "ACME CORPORATION - SERVICE AGREEMENT", fontsize=16)
        for i in range(30):
            page.insert_text((60, 110 + i * 20), f"Clause {i + 1}. The parties agree to the terms set out in "
                                                 f"schedule {i % 5 + 1} of this agreement.", fontsize=10)
        if stamp is not None and p == stamp_page:
            s = stamp.copy()
            alpha = s.split()[3].point(lambda a: int(a * opacity))
            s.putalpha(alpha)
            s = s.rotate(rotate, expand=True, resample=Image.BICUBIC)
            buf = io.BytesIO()
            s.save(buf, format="PNG")
            w = 595 * scale
            h = w * s.height / s.width
            x, y = 595 * pos[0], 842 * pos[1]
            page.insert_image(pymupdf.Rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2), stream=buf.getvalue())
            page.insert_text((60, 790), "Authorised signatory: ____________________", fontsize=10)
    doc.save(path)


def main() -> None:
    (ROOT / "stamps").mkdir(exist_ok=True)
    for name, img in REFERENCES.items():
        on_white(img).save(ROOT / "stamps" / f"{name}.png")
    (ROOT / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)
    on_white(UNKNOWN).save(ROOT / "tests" / "fixtures" / "unknown_stamp.png")

    out = ROOT / "stamp_samples"
    out.mkdir(exist_ok=True)
    make_pdf(out / "matched_finance_rotated.pdf", REFERENCES["finance_dept_seal"], rotate=23)
    make_pdf(out / "matched_hr_page2.pdf", REFERENCES["hr_received"], rotate=-8, page_count=3, stamp_page=1)
    make_pdf(out / "matched_legal_faded.pdf", REFERENCES["legal_seal"], rotate=140, opacity=0.55, scale=0.25)
    make_pdf(out / "unknown_stamp.pdf", UNKNOWN, rotate=10)
    make_pdf(out / "no_stamp.pdf", None)
    print(f"Wrote {len(REFERENCES)} references to backend/stamps/, 1 fixture, 5 sample PDFs to backend/stamp_samples/")


if __name__ == "__main__":
    main()
