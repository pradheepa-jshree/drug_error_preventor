"""
Member 1 — dataset loading for TrOCR fine-tuning.

Expected structure:

data/train/
    images/
        img_0001.png
        img_0002.png
    labels.csv

data/val/
    images/
        img_0003.png
        img_0004.png
    labels.csv

labels.csv must contain:

filename,text

Example:

img_0001.png,Amlodipine 5mg
img_0002.png,Losartan 50mg
"""

import os
import csv

from PIL import Image
import torch
from torch.utils.data import Dataset

from .trocr_inference import preprocess as image_preprocess


class HandwritingOCRDataset(Dataset):

    def __init__(
        self,
        data_dir: str,
        processor,
        max_target_length: int = 32
    ):

        self.data_dir = data_dir

        self.images_dir = os.path.join(
            data_dir,
            "images"
        )

        self.processor = processor

        self.max_target_length = max_target_length

        self.samples = self._load_and_validate(
            os.path.join(
                data_dir,
                "labels.csv"
            )
        )

        if len(self.samples) == 0:
            raise ValueError(
                f"No valid samples found in {data_dir}."
            )

    def _load_and_validate(
        self,
        labels_path: str
    ) -> list[tuple[str, str]]:

        if not os.path.isfile(labels_path):
            raise FileNotFoundError(
                f"labels.csv not found at {labels_path}"
            )

        samples = []
        skipped = 0

        with open(
            labels_path,
            newline="",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            required_cols = {
                "filename",
                "text"
            }

            actual_cols = {
                c.strip().lower()
                for c in (reader.fieldnames or [])
            }

            if not required_cols.issubset(actual_cols):

                raise ValueError(
                    "labels.csv must have columns "
                    "'filename' and 'text'. "
                    f"Found: {reader.fieldnames}"
                )

            for row_num, row in enumerate(
                reader,
                start=2
            ):

                filename = (
                    row.get("filename") or ""
                ).strip()

                text = (
                    row.get("text") or ""
                ).strip()

                if not filename or not text:

                    print(
                        f"[dataset] Skipping row "
                        f"{row_num}: empty filename or text."
                    )

                    skipped += 1
                    continue

                image_path = os.path.join(
                    self.images_dir,
                    filename
                )

                if not os.path.isfile(image_path):

                    print(
                        f"[dataset] Skipping row "
                        f"{row_num}: image not found "
                        f"at {image_path}"
                    )

                    skipped += 1
                    continue

                samples.append(
                    (image_path, text)
                )

        print(
            f"[dataset] Loaded {len(samples)} valid samples "
            f"from {labels_path} "
            f"({skipped} skipped)."
        )

        return samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):

        image_path, text = self.samples[idx]

        with open(
            image_path,
            "rb"
        ) as f:

            image_bytes = f.read()

        img = image_preprocess(
            image_bytes
        )

        pixel_values = self.processor(
            images=img,
            return_tensors="pt"
        ).pixel_values.squeeze(0)

        labels = self.processor.tokenizer(
            text,
            padding="max_length",
            max_length=self.max_target_length,
            truncation=True
        ).input_ids

        labels = [
            label
            if label != self.processor.tokenizer.pad_token_id
            else -100
            for label in labels
        ]

        return {
            "pixel_values": pixel_values,
            "labels": torch.tensor(labels)
        }


def collate_fn(batch):

    pixel_values = torch.stack(
        [
            item["pixel_values"]
            for item in batch
        ]
    )

    labels = torch.stack(
        [
            item["labels"]
            for item in batch
        ]
    )

    return {
        "pixel_values": pixel_values,
        "labels": labels
    }
