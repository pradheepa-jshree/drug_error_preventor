"""
Member 1 — thin integration wrapper between the backend
and the TrOCR pipeline.
"""

import os
import sys


PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        ".."
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )


from ml.ocr.trocr_inference import run_ocr
from .text_parser import parse_ocr_text


def process_prescription_line_image(
    image_bytes: bytes
) -> dict:

    ocr_result = run_ocr(
        image_bytes
    )

    parsed = parse_ocr_text(
        ocr_result["raw_text"]
    )

    return {
        "raw_text": ocr_result["raw_text"],
        "ocr_confidence": ocr_result["confidence"],
        "used_adapter": ocr_result["used_adapter"],
        "medicine_name": parsed["medicine_name"],
        "dosage_mg": parsed["dosage_mg"],
        "frequency": parsed["frequency"],
    }