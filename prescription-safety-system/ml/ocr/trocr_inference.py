"""
TrOCR inference for handwritten prescription images.
Uses a PRETRAINED model (microsoft/trocr-base-handwritten) — not
trained from scratch, and not fine-tuned per doctor. See
trocr_lora_scaffold.py for the future personalization plan.
"""

from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import cv2
import numpy as np

# Loaded once at import time. First run downloads weights from
# Hugging Face — this needs internet access. Test this on Day 1.
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")


def preprocess(image_path: str) -> Image.Image:
    """
    Cleans up a handwritten prescription photo before OCR:
    grayscale + adaptive threshold to boost contrast on messy
    handwriting / uneven lighting from a phone photo.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Could not read image at {image_path}")

    img = cv2.adaptiveThreshold(
        img, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 15,
    )
    return Image.fromarray(img).convert("RGB")


def run_ocr(image_path: str) -> dict:
    """
    Runs TrOCR on a single prescription line/image and returns the
    predicted text plus a confidence proxy derived from the model's
    per-token generation scores.
    """
    img = preprocess(image_path)
    pixel_values = processor(images=img, return_tensors="pt").pixel_values

    out = model.generate(
        pixel_values,
        output_scores=True,
        return_dict_in_generate=True,
    )
    text = processor.batch_decode(out.sequences, skip_special_tokens=True)[0]

    # Confidence proxy: average of the max score per generated token.
    # Not a calibrated probability — just a relative signal for the
    # "low confidence -> route to pharmacist" rule.
    if out.scores:
        confidence = float(np.mean([s.max().item() for s in out.scores]))
    else:
        confidence = 0.0

    return {"text": text, "confidence": round(confidence, 3)}


if __name__ == "__main__":
    # Quick manual test — point this at a sample image in
    # sample_data/prescriptions/ once you have one.
    import sys
    if len(sys.argv) > 1:
        result = run_ocr(sys.argv[1])
        print(result)
    else:
        print("Usage: python trocr_inference.py <path_to_image>")
