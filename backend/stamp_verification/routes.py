"""Stamp endpoints: POST /api/v1/stamps/verify, GET /api/v1/stamps/references (logged-in users)."""
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from common import auth
from common.config import get_config
from common.security import verify_api_key
from stamp_verification.pdf_to_images import InvalidPdfError
from stamp_verification.pipeline import verify_pdf
from stamp_verification.references import list_references
from stamp_verification.schemas import ReferenceStamp, StampVerification

router = APIRouter(
    prefix="/stamps",
    tags=["stamp verification"],
    dependencies=[Depends(verify_api_key), Depends(auth.get_user_session)],
)


@router.post("/verify", response_model=StampVerification)
async def verify(file: UploadFile = File(...)):
    name = Path(file.filename or "document.pdf").name
    if Path(name).suffix.lower() != ".pdf":
        raise HTTPException(400, "Please upload a PDF file.")
    max_bytes = get_config("stamps.max_file_mb") * 1024 * 1024
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, f"The file is larger than {get_config('stamps.max_file_mb')} MB.")
    try:
        # Rendering + image processing is CPU-heavy: run it in a thread so other requests aren't stuck
        return await run_in_threadpool(verify_pdf, data, name)
    except InvalidPdfError as e:
        raise HTTPException(400, str(e))


@router.get("/references", response_model=list[ReferenceStamp])
async def references():
    return await run_in_threadpool(list_references, get_config("stamps.references_dir"))
