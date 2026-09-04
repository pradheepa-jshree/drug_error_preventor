"""
Member 1 — rule-based OCR text parser.

Takes raw TrOCR output and extracts:
- medicine name
- dosage
- frequency

No ML is used here.
"""

import re


DOSAGE_RE = re.compile(
    r"(\d+\.?\d*)\s*(mg|ml|mcg)",
    re.I
)

FREQ_RE = re.compile(
    r"(\d)\s*[-x]\s*(\d)\s*[-x]\s*(\d)",
    re.I
)


def parse_ocr_text(raw_text: str) -> dict:
    """
    Parse raw OCR text into structured fields.
    """

    raw_text = (raw_text or "").strip()

    dosage_match = DOSAGE_RE.search(raw_text)
    freq_match = FREQ_RE.search(raw_text)

    medicine_name = DOSAGE_RE.sub(
        "",
        raw_text
    )

    medicine_name = FREQ_RE.sub(
        "",
        medicine_name
    )

    medicine_name = medicine_name.strip()

    return {
        "medicine_name": medicine_name,
        "dosage_mg": (
            float(dosage_match.group(1))
            if dosage_match
            else None
        ),
        "frequency": (
            freq_match.group(0)
            if freq_match
            else None
        ),
    }


# Compatibility with the original guide's function name.
def parse_line(
    raw_text: str,
    confidence: float
) -> dict:

    parsed = parse_ocr_text(raw_text)

    dosage_match = DOSAGE_RE.search(raw_text)

    return {
        "medicine_name": parsed["medicine_name"],
        "dosage": (
            dosage_match.group(0)
            if dosage_match
            else None
        ),
        "frequency": parsed["frequency"],
        "ocr_confidence": confidence,
    }