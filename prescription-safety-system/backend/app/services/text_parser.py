"""
Regex/rule-based parsing of raw OCR text into structured fields.
No ML here on purpose — dosage and frequency patterns are
predictable enough that simple regex is more reliable and
explainable than a model guess.
"""

import re

# e.g. "5mg", "10 ml", "250mcg"
DOSAGE_RE = re.compile(r"(\d+\.?\d*)\s*(mg|ml|mcg)", re.I)

# e.g. "1-0-1" (morning-afternoon-night dosing pattern)
FREQ_RE = re.compile(r"(\d)\s*[-x]\s*(\d)\s*[-x]\s*(\d)")


def parse_line(raw_text: str, confidence: float) -> dict:
    """
    Takes one line of raw OCR output + its confidence score and
    extracts medicine name, dosage, and frequency as separate fields.
    """
    dosage_match = FREQ_RE and DOSAGE_RE.search(raw_text)
    freq_match = FREQ_RE.search(raw_text)

    # Strip the dosage substring out of the raw text to leave
    # (roughly) just the medicine name.
    medicine_name = DOSAGE_RE.sub("", raw_text).strip()

    return {
        "medicine_name": medicine_name,
        "dosage": dosage_match.group(0) if dosage_match else None,
        "frequency": freq_match.group(0) if freq_match else None,
        "ocr_confidence": confidence,
    }


if __name__ == "__main__":
    # Quick manual test
    sample = "Aml0dipine 5mg 1-0-1"
    print(parse_line(sample, confidence=0.71))
