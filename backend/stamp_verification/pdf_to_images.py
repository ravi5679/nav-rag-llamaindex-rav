"""Step 1 - Turn PDF pages into images (PyMuPDF).

Rendering (instead of extracting embedded images) catches every kind of stamp: scanned pages,
images pasted onto the page, and stamps drawn as vector graphics.
"""
import numpy as np
import pymupdf


class InvalidPdfError(Exception):
    pass


def render_pages(pdf_bytes: bytes, dpi: int, max_pages: int) -> list[np.ndarray]:
    """Return one BGR image (OpenCV's colour order) per page, at `dpi` resolution."""
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise InvalidPdfError("The file is not a readable PDF.") from e
    if doc.page_count == 0:
        raise InvalidPdfError("The PDF has no pages.")
    if doc.page_count > max_pages:
        raise InvalidPdfError(f"The PDF has {doc.page_count} pages; the limit is {max_pages}.")

    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
        rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        pages.append(rgb[:, :, ::-1].copy())   # RGB -> BGR
    doc.close()
    return pages
