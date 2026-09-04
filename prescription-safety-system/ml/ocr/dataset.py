from pathlib import Path

import pandas as pd
from PIL import Image
from torch.utils.data import Dataset


class HandwritingOCRDataset(Dataset):

    def __init__(self, root_dir, processor, max_target_length=64):
        self.root = Path(root_dir)
        self.processor = processor
        self.max_target_length = max_target_length

        self.image_dir = self.root / "images"
        self.labels_path = self.root / "labels.csv"

        if not self.labels_path.exists():
            raise FileNotFoundError(
                f"Missing labels file: {self.labels_path}"
            )

        if not self.image_dir.exists():
            raise FileNotFoundError(
                f"Missing image directory: {self.image_dir}"
            )

        df = pd.read_csv(self.labels_path)

        if "filename" not in df.columns or "text" not in df.columns:
            raise ValueError(
                "labels.csv must contain columns: filename,text"
            )

        self.samples = []

        for _, row in df.iterrows():

            filename = str(row["filename"]).strip()
            text = str(row["text"]).strip()

            image_path = self.image_dir / filename

            if image_path.exists() and text:
                self.samples.append((image_path, text))

        print(
            f"[dataset] Loaded {len(self.samples)} valid samples "
            f"from {self.labels_path}"
        )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):

        image_path, text = self.samples[idx]

        image = Image.open(image_path).convert("RGB")

        pixel_values = self.processor(
            images=image,
            return_tensors="pt"
        ).pixel_values.squeeze(0)

        labels = self.processor.tokenizer(
            text,
            padding="max_length",
            max_length=self.max_target_length,
            truncation=True,
            return_tensors="pt"
        ).input_ids.squeeze(0)

        labels[
            labels == self.processor.tokenizer.pad_token_id
        ] = -100

        return {
            "pixel_values": pixel_values,
            "labels": labels,
        }