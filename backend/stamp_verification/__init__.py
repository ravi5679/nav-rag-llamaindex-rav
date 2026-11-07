"""Stamp verification: find official stamps in a PDF and match them against reference stamps.

  1. pdf_to_images.py   render each page to an image          (PyMuPDF)
  2. detect.py          find stamp-like regions                (OpenCV: colour + shape)
  3. references.py      load reference stamps, precompute features
  4. match.py           compare a detected stamp to references (SIFT + RANSAC + overlap)
  5. pipeline.py        run 1-4 and decide Matched / Unknown Stamp / No Stamp
     routes.py          POST /api/v1/stamps/verify, GET /api/v1/stamps/references
"""
