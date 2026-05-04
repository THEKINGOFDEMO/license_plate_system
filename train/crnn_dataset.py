"""Dataset and charset utilities for CCPD CRNN training."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
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


@dataclass
class ManifestSummary:
    manifest_path: str
    num_samples: int
    unique_characters: List[str]
    charset_size: int
    max_label_length: int
    min_label_length: int
    avg_label_length: float


class CRNNCharset:
    """Character encoder/decoder for CCPD plate text."""

    def __init__(self, characters: Optional[Sequence[str]] = None) -> None:
        chars = list(characters or DEFAULT_CHARSET)
        if len(chars) != len(set(chars)):
            raise ValueError("Charset contains duplicate characters.")
        if "" in chars:
            raise ValueError("Charset cannot contain an empty character.")

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

    def decode_encoded_text(self, encoded: Sequence[int]) -> str:
        decoded: List[str] = []
        for index in encoded:
            if index == self.blank_index:
                raise ValueError("Blank index cannot appear in an encoded ground-truth label.")
            if index not in self.index_to_char:
                raise ValueError(f"Encoded label index {index} is outside the charset mapping.")
            decoded.append(self.index_to_char[index])
        return "".join(decoded)

    def decode_indices(self, indices: Sequence[int], collapse_repeats: bool = True) -> str:
        decoded: List[str] = []
        previous: Optional[int] = None
        for index in indices:
            if index == self.blank_index:
                previous = None
                continue
            if index not in self.index_to_char:
                raise ValueError(f"Predicted index {index} is outside the charset mapping.")
            if collapse_repeats and previous == index:
                continue
            decoded.append(self.index_to_char[index])
            previous = index
        return "".join(decoded)

    def to_json_dict(self) -> Dict[str, object]:
        return {
            "blank_index": self.blank_index,
            "num_classes": self.num_classes,
            "characters": self.characters,
            "char_to_index": self.char_to_index,
            "index_to_char": {str(index): char for index, char in self.index_to_char.items()},
        }

    def save_json(self, output_path: str | Path) -> None:
        path = Path(output_path)
        path.write_text(json.dumps(self.to_json_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


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


def build_charset_from_records(records: Sequence[SampleRecord], fallback_charset: Optional[Sequence[str]] = None) -> CRNNCharset:
    fallback = list(fallback_charset or DEFAULT_CHARSET)
    fallback_set = set(fallback)

    ordered_chars: List[str] = []
    present_chars = {char for record in records for char in record.label_text}

    for char in fallback:
        if char in present_chars:
            ordered_chars.append(char)

    missing = sorted(present_chars - fallback_set)
    ordered_chars.extend(missing)
    return CRNNCharset(ordered_chars)


def build_charset_from_manifests(
    data_root: str | Path,
    manifest_paths: Sequence[str | Path],
    fallback_charset: Optional[Sequence[str]] = None,
) -> CRNNCharset:
    records: List[SampleRecord] = []
    for manifest_path in manifest_paths:
        records.extend(load_manifest(data_root=data_root, manifest_path=manifest_path))
    return build_charset_from_records(records=records, fallback_charset=fallback_charset)


def summarize_manifest(records: Sequence[SampleRecord], manifest_path: str | Path) -> ManifestSummary:
    label_lengths = [len(record.label_text) for record in records]
    unique_characters = sorted({char for record in records for char in record.label_text})
    return ManifestSummary(
        manifest_path=str(manifest_path),
        num_samples=len(records),
        unique_characters=unique_characters,
        charset_size=len(unique_characters),
        max_label_length=max(label_lengths),
        min_label_length=min(label_lengths),
        avg_label_length=sum(label_lengths) / len(label_lengths),
    )


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
        max_samples: Optional[int] = None,
        sample_seed: int = 42,
    ) -> None:
        self.data_root = Path(data_root)
        self.records = load_manifest(data_root=self.data_root, manifest_path=manifest_path)
        if max_samples is not None:
            if max_samples <= 0:
                raise ValueError("max_samples must be positive when provided.")
            if max_samples < len(self.records):
                random.Random(sample_seed).shuffle(self.records)
                self.records = self.records[:max_samples]
        self.charset = charset
        self.img_height = img_height
        self.img_width = img_width
        self.grayscale = grayscale
        self.channels = 1 if grayscale else 3

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> Dict[str, object]:
        record = self.records[index]
        image_tensor, image_size = self._load_image(record.image_path)
        encoded_label = self.charset.encode(record.label_text)
        return {
            "image": image_tensor,
            "target": torch.tensor(encoded_label, dtype=torch.long),
            "target_length": len(encoded_label),
            "text": record.label_text,
            "image_path": str(record.image_path),
            "image_rel_path": record.image_rel_path,
            "encoded_label": encoded_label,
            "original_size": image_size,
        }

    def _load_image(self, image_path: Path) -> Tuple[torch.Tensor, Tuple[int, int]]:
        if not image_path.exists():
            raise FileNotFoundError(f"CRNN image file not found: {image_path}")

        image_mode = "L" if self.grayscale else "RGB"
        with Image.open(image_path) as image:
            original_size = image.size
            image = image.convert(image_mode)
            image = image.resize((self.img_width, self.img_height), Image.BILINEAR)
            array = np.asarray(image, dtype=np.float32) / 255.0

        if self.grayscale:
            array = np.expand_dims(array, axis=0)
        else:
            array = np.transpose(array, (2, 0, 1))
        return torch.from_numpy(array), original_size

    def get_debug_records(self, count: int = 10) -> List[Dict[str, object]]:
        debug_items: List[Dict[str, object]] = []
        for record in self.records[:count]:
            _, original_size = self._load_image(record.image_path)
            encoded_label = self.charset.encode(record.label_text)
            debug_items.append(
                {
                    "image_rel_path": record.image_rel_path,
                    "image_path": str(record.image_path),
                    "original_size": original_size,
                    "resized_size": (self.img_width, self.img_height),
                    "label_text": record.label_text,
                    "encoded_label": encoded_label,
                }
            )
        return debug_items


def crnn_collate_fn(batch: Sequence[Dict[str, object]]) -> Dict[str, object]:
    images = torch.stack([item["image"] for item in batch])  # type: ignore[index]
    targets = torch.cat([item["target"] for item in batch])  # type: ignore[index]
    target_lengths = torch.tensor([item["target_length"] for item in batch], dtype=torch.long)  # type: ignore[index]
    texts = [item["text"] for item in batch]  # type: ignore[index]
    image_paths = [item["image_path"] for item in batch]  # type: ignore[index]
    image_rel_paths = [item["image_rel_path"] for item in batch]  # type: ignore[index]
    encoded_labels = [item["encoded_label"] for item in batch]  # type: ignore[index]
    original_sizes = [item["original_size"] for item in batch]  # type: ignore[index]

    return {
        "images": images,
        "targets": targets,
        "target_lengths": target_lengths,
        "texts": texts,
        "image_paths": image_paths,
        "image_rel_paths": image_rel_paths,
        "encoded_labels": encoded_labels,
        "original_sizes": original_sizes,
    }


def decode_batch_predictions(logits: torch.Tensor, charset: CRNNCharset) -> List[str]:
    """Decode CRNN logits from [T, B, C] to a list of strings."""

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

        total_chars += len(target)
        for index, target_char in enumerate(target):
            pred_char = prediction[index] if index < len(prediction) else None
            if pred_char == target_char:
                correct_chars += 1

    char_accuracy = correct_chars / total_chars if total_chars else 0.0
    plate_accuracy = correct_plates / len(targets) if targets else 0.0
    return char_accuracy, plate_accuracy


def save_debug_records(debug_records: Sequence[Dict[str, object]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.write_text(json.dumps(list(debug_records), ensure_ascii=False, indent=2), encoding="utf-8")


def save_manifest_summary(summary: ManifestSummary, output_path: str | Path) -> None:
    path = Path(output_path)
    path.write_text(json.dumps(asdict(summary), ensure_ascii=False, indent=2), encoding="utf-8")
