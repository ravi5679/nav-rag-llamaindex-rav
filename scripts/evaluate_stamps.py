"""Measures stamp detection + matching accuracy on many generated variations.

Run from the repo root (after make_stamp_samples.py):
    uv run --directory backend python ../scripts/evaluate_stamps.py

For every reference stamp (and one unknown stamp) it builds PDFs with different rotations, sizes and
ink strengths, as clean PDFs and as simulated poor scans (100 dpi, blur, noise, JPEG q=35), runs the
real pipeline and prints accuracy + confidence distributions. Use the distributions to tune
STAMP_MATCH_THRESHOLD / STAMP_MATCH_MARGIN, ideally with your own real documents.
"""
import itertools
import logging
import random
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pymupdf

sys.path.insert(0, str(Path(__file__).parent))                        # make_stamp_samples
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))  # stamp_verification
import make_stamp_samples as gen  # noqa: E402
from stamp_verification.pipeline import verify_pdf  # noqa: E402

logging.disable(logging.INFO)


SCANS = {   # variant -> (dpi, JPEG quality, noise level)
    "scan": (200, 70, 4),        # a typical office scanner
    "poor_scan": (100, 35, 8),   # a bad phone photo / fax-like copy
}


def as_scan(pdf_path: Path, variant: str) -> Path:
    """Re-create the PDF as an image-only scan: lower dpi, blur, noise, JPEG compression."""
    dpi, quality, noise = SCANS[variant]
    pix = pymupdf.open(pdf_path)[0].get_pixmap(dpi=dpi)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = np.clip(img.astype(int) + np.random.normal(0, noise, img.shape), 0, 255).astype(np.uint8)
    _, jpg = cv2.imencode(".jpg", img[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, quality])
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(page.rect, stream=jpg.tobytes())
    out = pdf_path.with_suffix(f".{variant}.pdf")
    doc.save(out)
    return out


def main() -> None:
    random.seed(1)
    np.random.seed(1)
    stamps = {**gen.REFERENCES, "UNKNOWN": gen.UNKNOWN}
    tmp = Path(tempfile.mkdtemp())
    rows = []
    for name, rot, scale, opacity in itertools.product(stamps, [0, 15, 45, 90, 170, 300], [0.18, 0.25, 0.35], [0.5, 0.9]):
        pdf = tmp / f"{name}_{rot}_{scale}_{opacity}.pdf"
        gen.make_pdf(pdf, stamps[name], rotate=rot, scale=scale, opacity=opacity,
                     pos=(random.uniform(0.3, 0.7), random.uniform(0.25, 0.75)))
        for variant in ("clean", *SCANS):
            path = pdf if variant == "clean" else as_scan(pdf, variant)
            r = verify_pdf(path.read_bytes(), path.name)
            top = r["stamps"][0]["top_candidates"] if r["stamps"] else []
            wrong = next((t for t in top if t["reference"] != name), {"reference": None, "confidence": 0.0})
            rows.append({"truth": name, "variant": variant, "status": r["status"], "ref": r["matched_reference"],
                         "conf": r["confidence"], "runner_up": wrong["confidence"], "runner_up_ref": wrong["reference"],
                         "n": len(r["stamps"]), "case": (rot, scale, opacity)})

    for variant in ("clean", *SCANS):
        sel = [x for x in rows if x["variant"] == variant]
        known = [x for x in sel if x["truth"] != "UNKNOWN"]
        unknown = [x for x in sel if x["truth"] == "UNKNOWN"]
        correct = [x for x in known if x["status"] == "Matched" and x["ref"] == x["truth"]]
        wrong = [x for x in known if x["status"] == "Matched" and x["ref"] != x["truth"]]
        print(f"\n[{variant}] correct match: {len(correct)}/{len(known)}  |  WRONG match: {len(wrong)}  |  "
              f"unknown stamp -> 'Unknown Stamp': {sum(x['status'] == 'Unknown Stamp' for x in unknown)}/{len(unknown)}"
              f"  |  not detected: {sum(x['n'] == 0 for x in sel)}/{len(sel)}")
        tc = sorted(x["conf"] for x in correct)
        if tc:
            print(f"   true-match confidence: min {tc[0]:.2f}  p10 {tc[len(tc) // 10]:.2f}  median {tc[len(tc) // 2]:.2f}")
        worst = max(known, key=lambda x: x["runner_up"])
        print(f"   highest wrong-reference score: {worst['runner_up']:.2f} ({worst['truth']} scored as "
              f"{worst['runner_up_ref']}, case {worst['case']})  |  "
              f"highest unknown-stamp score: {max(x['conf'] for x in unknown):.2f}")
        for x in [x for x in known if x not in correct][:5]:
            print(f"   miss: {x['truth']} {x['case']} -> {x['status']} {x['ref']} ({x['conf']:.2f})")


if __name__ == "__main__":
    main()
