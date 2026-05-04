"""Dataset and charset utilities for CCPD CRNN training."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset


DEFAULT_CHARSET: List[str] = [
    "皖",
    "沪",
    "津",
    "渝",
    "冀",
    "晋",
    "蒙",
    "辽",
    "吉",
    "黑",
    "苏",
    "浙",
    "京",
    "闽",
    "赣",
    "鲁",
    "豫",
    "鄂",
    "湘",
    "粤",
    "桂",
    "琼",
    "川",
    "贵",
    "云",
    "藏",
    "陕",
    "甘",
    "青",
    "宁",
    "新",
    "警",
    "学",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "J",
    "K",
    "L",
    "M",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "O",
]


@dataclass
class SampleRecord:
    image_rel_path: str
    image_path: Path
    label_text: str


class CRNNCharset:
    """Character encoder/decoder for CCPD plate text."""

    def __init__(self, characters: Optional[Sequence[str]] = None) -> None:
        chars = list(characters or DEFAULT_CHARSET)
        if len(chars) != len(set(chars)):
            raise ValueError("Charset contains duplicate characters.")
        self.blank_index = 0
        self.characters = chars
        self.index_to_char: Dict[int, str] = {index + 1: char for index, char in enumerate(chars)}
        self.char_to_index: Dict[str, int] = {char: index for index, char in self.index_to_char.items()}

    @property
    def num_classes(self) -> int:
        return len(self.characters) + 1

    def encode(self, text: str) -> List[int]:
        encoded: List[int] = []
        for char in text:
            if char not in self.char_to_index:
                raise ValueError(f"Character '{char}' is not present in the CRNN charset.")
            encoded.append(self.char_to_index[char])
        return encoded

    def decode_indices(self, indices: Sequence[int], collapse_repeats: bool = True) -> str:
        decoded: List[str] = []
        previous = None
        for index in indices:
            if index == self.blank_index:
                previous = None
                continue
            if collapse_repeats and previous == index:
                continue
            decoded.append(self.index_to_char[index])
            previous = index
        return "".join(decoded)


def load_manifest(data_root: str | Path, manifest_path: str | Path) -> List[SampleRecord]:
    root = Path(data_root)
    manifest = Path(manifest_path)
    if not manifest.is_absolute():
        manifest = root / manifest
    manifest = manifest.resolve()

    if not manifest.exists():
        raise FileNotFoundError(f"CRNN manifest file not found: {manifest}")

    records: List[SampleRecord] = []
    with manifest.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                raise ValueError(
                    f"Invalid manifest line {line_number} in {manifest}. Expected '<relative_path> <plate_text>'."
                )
            image_rel_path = parts[0]
            label_text = parts[-1]
            image_path = (root / image_rel_path).resolve()
            records.append(
                SampleRecord(
                    image_rel_path=image_rel_path,
                    image_path=image_path,
                    label_text=label_text,
                )
            )
    if not records:
        raise ValueError(f"No valid samples found in manifest: {manifest}")
    return records


class CRNNDataset(Dataset):
    """CRNN dataset for cropped CCPD plate images."""

    def __init__(
        self,
        data_root: str | Path,
        manifest_path: str | Path,
        charset: CRNNCharset,
        img_height: int = 32,
        img_width: int = 160,
        grayscale: bool = True,
    ) -> None:
        self.data_root = Path(data_root)
        self.records = load_manifest(data_root=self.data_root, manifest_path=manifest_path)
        self.charset = charset
        self.img_height = img_height
        self.img_width = img_width
        self.grayscale = grayscale
        self.channels = 1 if grayscale else 3

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> Dict[str, object]:
        record = self.records[index]
        image_tensor = self._load_image(record.image_path)
        encoded_label = self.charset.encode(record.label_text)
        return {
            "image": image_tensor,
            "target": torch.tensor(encoded_label, dtype=torch.long),
            "target_length": len(encoded_label),
            "text": record.label_text,
            "image_path": str(record.image_path),
            "image_rel_path": record.image_rel_path,
        }

    def _load_image(self, image_path: Path) -> torch.Tensor:
        if not image_path.exists():
            raise FileNotFoundError(f"CRNN image file not found: {image_path}")

        image_mode = "L" if self.grayscale else "RGB"
        with Image.open(image_path) as image:
            image = image.convert(image_mode)
            image = image.resize((self.img_width, self.img_height), Image.BILINEAR)
            array = np.asarray(image, dtype=np.float32) / 255.0

        if self.grayscale:
            array = np.expand_dims(array, axis=0)
        else:
            array = np.transpose(array, (2, 0, 1))
        return torch.from_numpy(array)


def crnn_collate_fn(batch: Sequence[Dict[str, object]]) -> Dict[str, object]:
    images = torch.stack([item["image"] for item in batch])  # type: ignore[index]
    targets = torch.cat([item["target"] for item in batch])  # type: ignore[index]
    target_lengths = torch.tensor([item["target_length"] for item in batch], dtype=torch.long)  # type: ignore[index]
    texts = [item["text"] for item in batch]  # type: ignore[index]
    image_paths = [item["image_path"] for item in batch]  # type: ignore[index]
    image_rel_paths = [item["image_rel_path"] for item in batch]  # type: ignore[index]

    return {
        "images": images,
        "targets": targets,
        "target_lengths": target_lengths,
        "texts": texts,
        "image_paths": image_paths,
        "image_rel_paths": image_rel_paths,
    }


def decode_batch_predictions(logits: torch.Tensor, charset: CRNNCharset) -> List[str]:
    """Decode CRNN logits from [T, N, C] to a list of strings."""

    max_indices = logits.argmax(dim=2).transpose(0, 1).cpu().tolist()
    return [charset.decode_indices(indices) for indices in max_indices]


def compute_accuracy(predictions: Sequence[str], targets: Sequence[str]) -> Tuple[float, float]:
    """Return character accuracy and whole-plate accuracy."""

    total_chars = 0
    correct_chars = 0
    correct_plates = 0

    for prediction, target in zip(predictions, targets):
        if prediction == target:
            correct_plates += 1
        max_length = max(len(prediction), len(target))
        if max_length == 0:
            continue
        total_chars += max_length
        for index in range(max_length):
            pred_char = prediction[index] if index < len(prediction) else None
            target_char = target[index] if index < len(target) else None
            if pred_char == target_char:
                correct_chars += 1

    char_accuracy = correct_chars / total_chars if total_chars else 0.0
    plate_accuracy = correct_plates / len(targets) if targets else 0.0
    return char_accuracy, plate_accuracy
