"""
Service layer that ties together TrOCR inference + text parsing.
This is what the /ocr router calls — it doesn't know about FastAPI
or HTTP at all, just takes an image path and returns structured
results. Keeping this separate from the router makes it testable
on its own (see Section 13 of the build guide).
"""

import sys
import os

# Allow importing from ml/ocr/ (adjust if your folder layout differs)
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "ocr"))

from trocr_inference import run_ocr
from text_parser import parse_line


def process_prescription_image(image_path: str) -> dict:
    """
    Full OCR pipeline for one prescription image:
    raw image -> TrOCR text + confidence -> parsed structured fields.

    Returns the same shape the /ocr endpoint promises in Section 8
    of the build guide: {text, dosage, frequency, ocr_confidence}.
    """
    ocr_result = run_ocr(image_path)
    parsed = parse_line(ocr_result["text"], ocr_result["confidence"])

    return {
        "text": ocr_result["text"],
        "dosage": parsed["dosage"],
        "frequency": parsed["frequency"],
        "ocr_confidence": ocr_result["confidence"],
        "medicine_name": parsed["medicine_name"],
    }


# NOTE: The build guide's demo prescriptions may have multiple lines
# per image (multiple drugs). For the MVP, start with one line per
# image and extend to multi-line splitting later if time allows —
# don't block on this on Day 1.
