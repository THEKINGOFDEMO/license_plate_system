"""Utilities for parsing CCPD filenames and generating labels.

CCPD embeds all annotations directly in the image filename. The parser in this
module is based on the official CCPD annotation format:
https://github.com/detectRecog/CCPD
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple, Union


PROVINCES: List[str] = [
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
    "O",
]

ALPHABETS: List[str] = [
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
    "O",
]

ADS: List[str] = [
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


Point = Tuple[int, int]


@dataclass(frozen=True)
class CCPDAnnotation:
    """Structured metadata parsed from one CCPD filename."""

    source_path: Path
    area_ratio_raw: str
    area_ratio: float
    tilt_degrees: Tuple[int, int]
    bbox: Tuple[int, int, int, int]
    vertices: Tuple[Point, Point, Point, Point]
    plate_indices: Tuple[int, ...]
    plate_text: str
    brightness: int
    blurriness: int


def parse_ccpd_filename(path_like: Union[str, Path]) -> CCPDAnnotation:
    """Parse one CCPD filename into a structured annotation."""

    source_path = Path(path_like)
    stem = source_path.stem
    parts = stem.split("-")
    if len(parts) != 7:
        raise ValueError(
            "Invalid CCPD filename format for "
            f"'{source_path.name}'. Expected 7 '-' separated fields, got {len(parts)}."
        )

    area_raw, tilt_raw, bbox_raw, vertices_raw, plate_raw, brightness_raw, blur_raw = parts

    tilt = _parse_int_pair(tilt_raw, "_", "tilt", source_path.name)
    top_left, bottom_right = _parse_bbox(bbox_raw, source_path.name)
    vertices = _parse_vertices(vertices_raw, source_path.name)
    plate_indices = tuple(_parse_int_list(plate_raw, "_", "plate indices", source_path.name))
    plate_text = decode_plate_indices(plate_indices)

    return CCPDAnnotation(
        source_path=source_path,
        area_ratio_raw=area_raw,
        area_ratio=_parse_area_ratio(area_raw, source_path.name),
        tilt_degrees=tilt,
        bbox=(top_left[0], top_left[1], bottom_right[0], bottom_right[1]),
        vertices=vertices,
        plate_indices=plate_indices,
        plate_text=plate_text,
        brightness=_parse_single_int(brightness_raw, "brightness", source_path.name),
        blurriness=_parse_single_int(blur_raw, "blurriness", source_path.name),
    )


def decode_plate_indices(indices: Sequence[int]) -> str:
    """Decode CCPD plate indices into plate text.

    Standard blue plates have 7 characters, while CCPD-Green contains 8.
    We decode the first character from PROVINCES, the second from ALPHABETS,
    and the remaining characters from ADS.
    """

    if len(indices) < 2:
        raise ValueError(
            f"Invalid CCPD plate indices {list(indices)}. At least 2 indices are required."
        )

    decoded = [
        _lookup_charset(PROVINCES, indices[0], "province"),
        _lookup_charset(ALPHABETS, indices[1], "alphabet"),
    ]
    decoded.extend(_lookup_charset(ADS, value, "ads") for value in indices[2:])
    return "".join(decoded)


def yolo_bbox_from_annotation(annotation: CCPDAnnotation, image_width: int, image_height: int) -> Tuple[float, float, float, float]:
    """Convert a CCPD bounding box into YOLO normalized format."""

    x1, y1, x2, y2 = clamp_bbox(annotation.bbox, image_width, image_height)
    box_width = x2 - x1
    box_height = y2 - y1
    if box_width <= 0 or box_height <= 0:
        raise ValueError(
            f"Invalid bounding box {annotation.bbox} for '{annotation.source_path.name}' after clamping."
        )

    x_center = (x1 + x2) / 2.0 / image_width
    y_center = (y1 + y2) / 2.0 / image_height
    width = box_width / float(image_width)
    height = box_height / float(image_height)
    return x_center, y_center, width, height


def clamp_bbox(bbox: Tuple[int, int, int, int], image_width: int, image_height: int) -> Tuple[int, int, int, int]:
    """Clamp a bounding box to image bounds."""

    x1, y1, x2, y2 = bbox
    x1 = max(0, min(x1, image_width))
    x2 = max(0, min(x2, image_width))
    y1 = max(0, min(y1, image_height))
    y2 = max(0, min(y2, image_height))
    return x1, y1, x2, y2


def _parse_area_ratio(raw_value: str, filename: str) -> float:
    value = _parse_single_int(raw_value, "area ratio", filename)
    return value / 1000.0


def _parse_bbox(raw_value: str, filename: str) -> Tuple[Point, Point]:
    parts = raw_value.split("_")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid bbox field '{raw_value}' in '{filename}'. Expected 'x1&y1_x2&y2'."
        )
    return (
        _parse_point(parts[0], "bbox top-left", filename),
        _parse_point(parts[1], "bbox bottom-right", filename),
    )


def _parse_vertices(raw_value: str, filename: str) -> Tuple[Point, Point, Point, Point]:
    parts = raw_value.split("_")
    if len(parts) != 4:
        raise ValueError(
            f"Invalid vertices field '{raw_value}' in '{filename}'. Expected 4 points."
        )
    return tuple(_parse_point(part, "vertex", filename) for part in parts)  # type: ignore[return-value]


def _parse_point(raw_value: str, label: str, filename: str) -> Point:
    point = _parse_int_pair(raw_value, "&", label, filename)
    return point[0], point[1]


def _parse_int_pair(raw_value: str, separator: str, label: str, filename: str) -> Tuple[int, int]:
    parts = raw_value.split(separator)
    if len(parts) != 2:
        raise ValueError(
            f"Invalid {label} field '{raw_value}' in '{filename}'. Expected 2 values."
        )
    return (
        _parse_single_int(parts[0], label, filename),
        _parse_single_int(parts[1], label, filename),
    )


def _parse_int_list(raw_value: str, separator: str, label: str, filename: str) -> List[int]:
    return [_parse_single_int(part, label, filename) for part in raw_value.split(separator)]


def _parse_single_int(raw_value: str, label: str, filename: str) -> int:
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid {label} value '{raw_value}' in '{filename}'. Expected an integer."
        ) from exc


def _lookup_charset(charset: Sequence[str], index: int, label: str) -> str:
    if index < 0 or index >= len(charset):
        raise ValueError(
            f"Invalid CCPD {label} index {index}. Valid range is 0 to {len(charset) - 1}."
        )
    return charset[index]
