from fastapi import APIRouter, UploadFile, File
import shutil
import tempfile
import os

from app.services.ocr_service import process_prescription_image

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/ocr")
async def ocr_prescription(file: UploadFile = File(...)):
    """
    Accepts one prescription image, runs the OCR pipeline
    (TrOCR + text parsing), and returns the result.
    """
    suffix = os.path.splitext(file.filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = process_prescription_image(tmp_path)
    finally:
        os.remove(tmp_path)

    return [result]
