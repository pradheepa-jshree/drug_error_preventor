"""
FUTURE WORK — NOT TRAINED IN THIS HACKATHON.

This file documents where a doctor-specific LoRA/PEFT adapter would
attach to TrOCR, for the pitch. It does not run any training.

Why the decoder, not the encoder:
The encoder reads general image features (shapes, strokes) that are
common across all handwriting. The decoder is where the model turns
those features into text — this is where one doctor's specific
letter-formation quirks (e.g. how they write a lowercase 'a' or a
'5') would need to be learned. So a LoRA adapter targeting decoder
attention layers is the natural attachment point.

How it would work at inference time (future):
  1. Pharmacist corrections accumulate in the `ocr_corrections` table,
     tagged by doctor_id (this part IS built — see Section 6.7 of the
     build guide / the /feedback endpoint).
  2. Once enough corrections exist for a given doctor, a LoRA adapter
     is fine-tuned on that doctor's (original_ocr_text, corrected_text)
     pairs.
  3. Each doctor_id maps to one small adapter file — not a separate
     full copy of TrOCR per doctor.
  4. At inference time, the adapter for that prescription's doctor_id
     is loaded on top of the shared base TrOCR model.

Below is a DOCUMENTED, NOT-RUN sketch of what step 2 would look like
using PEFT's LoraConfig. Do not execute this during the hackathon.
"""

# from peft import LoraConfig, get_peft_model
# from transformers import VisionEncoderDecoderModel
#
# base_model = VisionEncoderDecoderModel.from_pretrained(
#     "microsoft/trocr-base-handwritten"
# )
#
# lora_config = LoraConfig(
#     r=8,
#     lora_alpha=16,
#     # Target the decoder's attention projections — this is the
#     # part responsible for generating text, not reading the image.
#     target_modules=["decoder.model.decoder.layers.*.self_attn.q_proj",
#                      "decoder.model.decoder.layers.*.self_attn.v_proj"],
#     lora_dropout=0.05,
#     bias="none",
# )
#
# doctor_specific_model = get_peft_model(base_model, lora_config)
#
# # Training would use (original_ocr_text, corrected_text) pairs
# # pulled from ocr_corrections WHERE doctor_id = <this doctor>,
# # once there are enough samples to be meaningful (not defined here
# # — a real threshold would need real data to tune).
#
# # doctor_specific_model.save_pretrained(f"adapters/doctor_{doctor_id}/")


def scaffold_notice() -> str:
    """
    Called nowhere in the pipeline — exists so this file has a
    runnable symbol if anyone imports it by mistake, and so the demo
    can show "yes, this file exists and is documented" without
    pretending it does anything yet.
    """
    return (
        "LoRA personalization is NOT trained in this MVP. "
        "See module docstring for the documented future plan."
    )


if __name__ == "__main__":
    print(scaffold_notice())
