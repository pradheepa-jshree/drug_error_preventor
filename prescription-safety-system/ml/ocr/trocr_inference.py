"""
Member 1 — TrOCR inference.

Loads the pretrained base model always. If a fine-tuned LoRA adapter
exists at ADAPTER_DIR, it's loaded on top; otherwise inference falls
back cleanly to the base pretrained model.
"""

import os
import numpy as np
from PIL import Image
import cv2
import torch


BASE_MODEL_NAME = "microsoft/trocr-base-handwritten"

ADAPTER_DIR = os.path.join(
    os.path.dirname(__file__),
    "trocr_lora_adapter"
)


_processor = None
_model = None
_using_adapter = False


def _load_model():
    global _processor, _model, _using_adapter

    if _model is not None:
        return _processor, _model

    from transformers import (
        TrOCRProcessor,
        VisionEncoderDecoderModel
    )

    _processor = TrOCRProcessor.from_pretrained(
        BASE_MODEL_NAME
    )

    base_model = VisionEncoderDecoderModel.from_pretrained(
        BASE_MODEL_NAME
    )

    adapter_config_path = os.path.join(
        ADAPTER_DIR,
        "adapter_config.json"
    )

    if os.path.isfile(adapter_config_path):
        try:
            from peft import PeftModel

            _model = PeftModel.from_pretrained(
                base_model,
                ADAPTER_DIR
            )

            _model.eval()
            _using_adapter = True

            print(
                f"[trocr_inference] Loaded fine-tuned adapter "
                f"from {ADAPTER_DIR}"
            )

        except Exception as e:
            print(
                f"[trocr_inference] WARNING: failed to load adapter "
                f"({e}). Falling back to base pretrained model."
            )

            _model = base_model
            _using_adapter = False

    else:
        _model = base_model
        _using_adapter = False

        print(
            "[trocr_inference] No fine-tuned adapter found — "
            "using base pretrained model."
        )

    return _processor, _model


def preprocess(image_bytes: bytes) -> Image.Image:
    """
    Grayscale + adaptive threshold.

    IMPORTANT:
    TrOCR expects a single text line.
    """

    arr = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )

    img = cv2.imdecode(
        arr,
        cv2.IMREAD_GRAYSCALE
    )

    if img is None:
        raise ValueError(
            "Could not decode image bytes — "
            "is this a valid image file?"
        )

    img = cv2.adaptiveThreshold(
        img,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15
    )

    return Image.fromarray(img).convert("RGB")


def run_ocr(image_bytes: bytes) -> dict:

    processor, model = _load_model()

    img = preprocess(image_bytes)

    pixel_values = processor(
        images=img,
        return_tensors="pt"
    ).pixel_values

    with torch.no_grad():

        out = model.generate(
            pixel_values,
            output_scores=True,
            return_dict_in_generate=True
        )

    text = processor.batch_decode(
        out.sequences,
        skip_special_tokens=True
    )[0]

    confidence = 0.0

    if out.scores:

        step_confidences = []

        for step_scores in out.scores:

            probs = torch.softmax(
                step_scores,
                dim=-1
            )

            step_confidences.append(
                probs.max().item()
            )

        if step_confidences:
            confidence = float(
                np.mean(step_confidences)
            )

    return {
        "raw_text": text.strip(),
        "confidence": round(confidence, 3),
        "used_adapter": _using_adapter,
    }
