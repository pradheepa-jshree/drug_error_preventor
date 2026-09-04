import argparse
from pathlib import Path

import torch

from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    default_data_collator,
)

from peft import LoraConfig, get_peft_model

from ml.ocr.dataset import HandwritingOCRDataset


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = "microsoft/trocr-small-handwritten"


# ============================================================
# BUILD LoRA MODEL
# ============================================================

def build_model(
    model_name,
    r=8,
    alpha=16,
    dropout=0.05,
    target_modules=None,
):
    """
    Load TrOCR and attach a LoRA adapter.
    """

    print("[model] Loading TrOCR...")

    # Load pretrained TrOCR
    model = VisionEncoderDecoderModel.from_pretrained(model_name)

    # --------------------------------------------------------
    # Required TrOCR configuration
    # --------------------------------------------------------

    model.config.decoder_start_token_id = (
        model.config.decoder.decoder_start_token_id
        if getattr(model.config.decoder, "decoder_start_token_id", None)
        is not None
        else 0
    )

    model.config.pad_token_id = (
        model.config.decoder.pad_token_id
        if getattr(model.config.decoder, "pad_token_id", None)
        is not None
        else 1
    )

    model.config.eos_token_id = (
        model.config.decoder.eos_token_id
        if getattr(model.config.decoder, "eos_token_id", None)
        is not None
        else 2
    )

    # Make sure decoder_start_token_id is definitely available
    if model.config.decoder_start_token_id is None:
        model.config.decoder_start_token_id = model.config.eos_token_id

    # Disable cache during training
    model.config.use_cache = False

    # --------------------------------------------------------
    # LoRA configuration
    # --------------------------------------------------------

    lora_config = LoraConfig(
        r=r,
        lora_alpha=alpha,
        lora_dropout=dropout,
        bias="none",
        target_modules=(
            target_modules
            if target_modules
            else r".*decoder.*(q_proj|v_proj)"
        ),
    )

    # Attach LoRA
    model = get_peft_model(model, lora_config)

    print("[model] LoRA model created successfully")

    model.print_trainable_parameters()

    return model


# ============================================================
# TRAIN
# ============================================================

def train(args):

    # --------------------------------------------------------
    # Device
    # --------------------------------------------------------

    device = "cuda" if torch.cuda.is_available() else "cpu"

    print()
    print("=" * 60)
    print(f"[train] Using device: {device}")
    print("=" * 60)

    # --------------------------------------------------------
    # Paths
    # --------------------------------------------------------

    train_dir = Path(args.train_dir)
    val_dir = Path(args.val_dir)
    output_dir = Path(args.output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(f"[path] Train directory: {train_dir}")
    print(f"[path] Validation directory: {val_dir}")
    print(f"[path] Output directory: {output_dir}")

    # --------------------------------------------------------
    # Load processor
    # --------------------------------------------------------

    print()
    print("[processor] Loading TrOCR processor...")

    processor = TrOCRProcessor.from_pretrained(
        MODEL_NAME
    )

    print("[processor] Processor loaded successfully")

    # --------------------------------------------------------
    # Load training dataset
    # --------------------------------------------------------

    print()
    print("[dataset] Loading training dataset...")

    train_dataset = HandwritingOCRDataset(
        root_dir=train_dir,
        processor=processor,
        max_target_length=args.max_target_length,
    )

    # --------------------------------------------------------
    # Load validation dataset
    # --------------------------------------------------------

    print()
    print("[dataset] Loading validation dataset...")

    val_dataset = HandwritingOCRDataset(
        root_dir=val_dir,
        processor=processor,
        max_target_length=args.max_target_length,
    )

    print()
    print(f"[dataset] Training samples: {len(train_dataset)}")
    print(f"[dataset] Validation samples: {len(val_dataset)}")

    # --------------------------------------------------------
    # Check datasets
    # --------------------------------------------------------

    if len(train_dataset) == 0:
        raise ValueError(
            "Training dataset is empty. "
            "Check data/train/images and data/train/labels.csv"
        )

    if len(val_dataset) == 0:
        raise ValueError(
            "Validation dataset is empty. "
            "Check data/val/images and data/val/labels.csv"
        )

    # --------------------------------------------------------
    # Build model
    # --------------------------------------------------------

    print()
    print("[model] Building LoRA model...")

    model = build_model(
        MODEL_NAME,
        r=args.lora_r,
        alpha=args.lora_alpha,
        dropout=args.lora_dropout,
        target_modules=args.target_modules,
    )

    # --------------------------------------------------------
    # Training arguments
    # --------------------------------------------------------

    print()
    print("[train] Preparing training configuration...")

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(output_dir),

        # Epochs
        num_train_epochs=args.epochs,

        # Batch size
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,

        # Learning rate
        learning_rate=args.learning_rate,

        # Logging
        logging_steps=1,

        # Evaluation
        eval_strategy="epoch",

        # Save model after each epoch
        save_strategy="epoch",

        save_total_limit=2,

        # Important for our custom dataset
        remove_unused_columns=False,

        # No external logging service
        report_to=[],

        # Only use FP16 when CUDA exists
        fp16=torch.cuda.is_available(),

        # Generate text during evaluation
        predict_with_generate=True,

        # Don't automatically select best model
        load_best_model_at_end=False,

        # CPU-friendly
        dataloader_num_workers=0,
    )

    # --------------------------------------------------------
    # Trainer
    # --------------------------------------------------------

    print()
    print("[trainer] Creating Seq2SeqTrainer...")

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=default_data_collator,
        processing_class=processor,
    )

    # --------------------------------------------------------
    # Start training
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("STARTING TrOCR LoRA TRAINING")
    print("=" * 60)
    print()

    trainer.train()

    # --------------------------------------------------------
    # Save adapter
    # --------------------------------------------------------

    print()
    print("[save] Saving LoRA adapter...")

    model.save_pretrained(
        str(output_dir)
    )

    # --------------------------------------------------------
    # Save processor
    # --------------------------------------------------------

    print("[save] Saving processor...")

    processor.save_pretrained(
        str(output_dir)
    )

    # --------------------------------------------------------
    # Finished
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("TRAINING COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print()

    print(f"Adapter saved to:")
    print(output_dir)

    print()


# ============================================================
# ARGUMENTS
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Fine-tune TrOCR using LoRA "
            "on handwritten prescription data."
        )
    )

    # --------------------------------------------------------
    # Dataset paths
    # --------------------------------------------------------

    parser.add_argument(
        "--train_dir",
        type=str,
        default="data/train",
        help="Training dataset directory",
    )

    parser.add_argument(
        "--val_dir",
        type=str,
        default="data/val",
        help="Validation dataset directory",
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    parser.add_argument(
        "--output_dir",
        type=str,
        default="ml/ocr/trocr_lora_adapter",
        help="Directory where LoRA adapter will be saved",
    )

    # --------------------------------------------------------
    # Training
    # --------------------------------------------------------

    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs",
    )

    parser.add_argument(
        "--batch_size",
        type=int,
        default=1,
        help="Training and validation batch size",
    )

    parser.add_argument(
        "--learning_rate",
        type=float,
        default=5e-5,
        help="Learning rate",
    )

    # --------------------------------------------------------
    # LoRA
    # --------------------------------------------------------

    parser.add_argument(
        "--lora_r",
        type=int,
        default=8,
        help="LoRA rank",
    )

    parser.add_argument(
        "--lora_alpha",
        type=int,
        default=16,
        help="LoRA alpha",
    )

    parser.add_argument(
        "--lora_dropout",
        type=float,
        default=0.05,
        help="LoRA dropout",
    )

    parser.add_argument(
        "--target_modules",
        type=str,
        default=None,
        help="Optional LoRA target module regex",
    )

    # --------------------------------------------------------
    # Tokenization
    # --------------------------------------------------------

    parser.add_argument(
        "--max_target_length",
        type=int,
        default=64,
        help="Maximum target text length",
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    args = parse_args()

    train(args)