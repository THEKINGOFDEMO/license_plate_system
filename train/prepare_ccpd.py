"""Prepare CCPD data for YOLO detection and CRNN recognition.

Example:
    python train/prepare_ccpd.py --src datasets/CCPD2019/ccpd_base --out . --limit 100 --make-yolo --make-crnn --preview 10
"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

try:
    from train.ccpd_utils import CCPDAnnotation, clamp_bbox, parse_ccpd_filename, yolo_bbox_from_annotation
except ImportError:
    from ccpd_utils import CCPDAnnotation, clamp_bbox, parse_ccpd_filename, yolo_bbox_from_annotation


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


@dataclass
class PreparedSample:
    image_path: Path
    annotation: CCPDAnnotation


@dataclass
class PreparedSplit:
    name: str
    samples: List[PreparedSample]


@dataclass
class SkippedFile:
    image_path: Path
    reason: str


@dataclass
class ConversionStats:
    candidate_images: int = 0
    selected_images: int = 0
    valid_samples: int = 0
    skipped_files: int = 0
    split_counts: Dict[str, int] = field(default_factory=lambda: {"train": 0, "val": 0, "test": 0})
    yolo_labels_written: int = 0
    crnn_crops_written: int = 0
    preview_images_written: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare CCPD dataset for YOLO and CRNN.")
    parser.add_argument("--src", required=True, help="Path to a CCPD image directory.")
    parser.add_argument("--out", required=True, help="Output root directory.")
    parser.add_argument("--limit", type=int, default=None, help="Optional max number of images to process.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible sampling and splitting.")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Train split ratio.")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Validation split ratio.")
    parser.add_argument("--test-ratio", type=float, default=0.1, help="Test split ratio.")
    parser.add_argument("--make-yolo", action="store_true", help="Generate YOLO images, labels, and dataset yaml.")
    parser.add_argument("--make-crnn", action="store_true", help="Generate cropped plate images and text labels for CRNN.")
    parser.add_argument("--dry-run", action="store_true", help="Only parse filenames and print the first 5 parsed samples without writing files.")
    parser.add_argument("--preview", type=int, default=0, help="Randomly save N preview images with bbox overlays to outputs/preview.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.dry_run and args.preview:
        parser.error("--dry-run cannot be combined with --preview because preview writes files.")

    if args.preview < 0:
        parser.error("--preview must be greater than or equal to 0.")

    if not args.dry_run and not args.make_yolo and not args.make_crnn and args.preview <= 0:
        parser.error(
            "Select at least one action: --make-yolo, --make-crnn, --preview N, or use --dry-run."
        )

    validate_ratios(args.train_ratio, args.val_ratio, args.test_ratio)

    src_dir = Path(args.src).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    stats = ConversionStats()

    image_paths = collect_image_paths(src_dir)
    stats.candidate_images = len(image_paths)

    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError("--limit must be a positive integer when provided.")
        image_paths = sample_image_paths(image_paths=image_paths, limit=args.limit, seed=args.seed)
        print(f"[prepare_ccpd] Applying limit: processing {len(image_paths)} sampled images.")

    stats.selected_images = len(image_paths)
    samples, skipped = collect_parsed_samples(image_paths)
    stats.valid_samples = len(samples)
    stats.skipped_files = len(skipped)
    print_skipped_summary(skipped)

    if args.dry_run:
        print("[prepare_ccpd] Dry run mode enabled. No files will be copied or generated.")
        print_dry_run_preview(samples)
        print_stats(stats)
        print("[prepare_ccpd] Done.")
        return 0

    splits = split_samples(
        samples=samples,
        seed=args.seed,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
    )
    stats.split_counts = {split.name: len(split.samples) for split in splits}
    print(
        "[prepare_ccpd] Split sizes: "
        + ", ".join(f"{split.name}={len(split.samples)}" for split in splits)
    )

    if args.make_yolo:
        generate_yolo_dataset(splits, out_dir, stats)

    if args.make_crnn:
        generate_crnn_dataset(splits, out_dir, stats)

    if args.preview > 0:
        generate_preview_images(samples=samples, out_dir=out_dir, preview_count=args.preview, seed=args.seed, stats=stats)

    print_stats(stats)
    print("[prepare_ccpd] Done.")
    return 0


def validate_ratios(train_ratio: float, val_ratio: float, test_ratio: float) -> None:
    values = {"train": train_ratio, "val": val_ratio, "test": test_ratio}
    for name, value in values.items():
        if value < 0:
            raise ValueError(f"{name} ratio must be non-negative, got {value}.")

    total = train_ratio + val_ratio + test_ratio
    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"Split ratios must sum to 1.0, got {total:.6f} "
            f"(train={train_ratio}, val={val_ratio}, test={test_ratio})."
        )


def collect_image_paths(src_dir: Path) -> List[Path]:
    if not src_dir.exists():
        raise FileNotFoundError(
            f"CCPD source directory does not exist: {src_dir}. "
            "Please check --src and make sure the dataset has been downloaded."
        )
    if not src_dir.is_dir():
        raise NotADirectoryError(f"CCPD source path is not a directory: {src_dir}")

    image_paths = sorted(
        path
        for path in src_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    if not image_paths:
        raise FileNotFoundError(
            f"No image files were found under {src_dir}. "
            "Expected CCPD images with suffixes: .jpg, .jpeg, .png, .bmp."
        )

    print(f"[prepare_ccpd] Found {len(image_paths)} candidate images under {src_dir}.")
    return image_paths


def collect_parsed_samples(image_paths: Sequence[Path]) -> Tuple[List[PreparedSample], List[SkippedFile]]:
    samples: List[PreparedSample] = []
    skipped: List[SkippedFile] = []

    for image_path in image_paths:
        try:
            annotation = parse_ccpd_filename(image_path.name)
        except ValueError as exc:
            skipped.append(SkippedFile(image_path=image_path, reason=str(exc)))
            continue
        samples.append(PreparedSample(image_path=image_path, annotation=annotation))

    print(
        f"[prepare_ccpd] Parsed {len(samples)} valid filenames, skipped {len(skipped)} invalid filenames."
    )
    return samples, skipped


def split_samples(
    samples: Sequence[PreparedSample],
    seed: int,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
) -> List[PreparedSplit]:
    del test_ratio  # The remainder is assigned to test.

    shuffled = list(samples)
    random.Random(seed).shuffle(shuffled)

    total = len(shuffled)
    train_count = int(total * train_ratio)
    val_count = int(total * val_ratio)

    train_samples = shuffled[:train_count]
    val_samples = shuffled[train_count : train_count + val_count]
    test_samples = shuffled[train_count + val_count :]

    return [
        PreparedSplit("train", train_samples),
        PreparedSplit("val", val_samples),
        PreparedSplit("test", test_samples),
    ]


def sample_image_paths(image_paths: Sequence[Path], limit: int, seed: int) -> List[Path]:
    if limit >= len(image_paths):
        return list(image_paths)

    sampled = list(image_paths)
    random.Random(seed).shuffle(sampled)
    return sampled[:limit]


def generate_yolo_dataset(splits: Sequence[PreparedSplit], out_dir: Path, stats: ConversionStats) -> None:
    image_module, _ = load_pillow_modules()

    for split in splits:
        image_out_dir = out_dir / "images" / split.name
        label_out_dir = out_dir / "labels" / split.name
        image_out_dir.mkdir(parents=True, exist_ok=True)
        label_out_dir.mkdir(parents=True, exist_ok=True)

        written = 0
        for sample in split.samples:
            try:
                with image_module.open(sample.image_path) as image:
                    width, height = image.size

                x_center, y_center, box_width, box_height = yolo_bbox_from_annotation(
                    annotation=sample.annotation,
                    image_width=width,
                    image_height=height,
                )
                label_line = f"0 {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}\n"

                output_image_path = image_out_dir / sample.image_path.name
                output_label_path = label_out_dir / f"{sample.image_path.stem}.txt"
                shutil.copy2(sample.image_path, output_image_path)
                output_label_path.write_text(label_line, encoding="utf-8")
                written += 1
            except (OSError, ValueError) as exc:
                stats.skipped_files += 1
                print(f"[prepare_ccpd] WARNING: skipped YOLO sample {sample.image_path.name}: {exc}")

        stats.yolo_labels_written += written
        print(f"[prepare_ccpd] YOLO {split.name}: wrote {written} images and labels.")

    write_yolo_config(out_dir)


def generate_crnn_dataset(splits: Sequence[PreparedSplit], out_dir: Path, stats: ConversionStats) -> None:
    image_module, _ = load_pillow_modules()
    crnn_root = out_dir / "crnn"
    crnn_root.mkdir(parents=True, exist_ok=True)

    for split in splits:
        image_out_dir = crnn_root / "images" / split.name
        image_out_dir.mkdir(parents=True, exist_ok=True)

        manifest_lines: List[str] = []
        written = 0
        for sample in split.samples:
            try:
                with image_module.open(sample.image_path) as image:
                    width, height = image.size
                    x1, y1, x2, y2 = clamp_bbox(sample.annotation.bbox, width, height)
                    if x2 <= x1 or y2 <= y1:
                        raise ValueError(
                            f"Invalid crop box {sample.annotation.bbox} for '{sample.image_path.name}' after clamping."
                        )

                    crop = image.crop((x1, y1, x2, y2))
                    output_image_path = image_out_dir / sample.image_path.name
                    crop.save(output_image_path)

                relative_image_path = Path("images") / split.name / sample.image_path.name
                manifest_lines.append(f"{relative_image_path.as_posix()}\t{sample.annotation.plate_text}")
                written += 1
            except (OSError, ValueError) as exc:
                stats.skipped_files += 1
                print(f"[prepare_ccpd] WARNING: skipped CRNN sample {sample.image_path.name}: {exc}")

        manifest_path = crnn_root / f"{split.name}.txt"
        manifest_path.write_text("\n".join(manifest_lines) + ("\n" if manifest_lines else ""), encoding="utf-8")
        stats.crnn_crops_written += written
        print(f"[prepare_ccpd] CRNN {split.name}: wrote {written} crops and manifest.")


def generate_preview_images(
    samples: Sequence[PreparedSample],
    out_dir: Path,
    preview_count: int,
    seed: int,
    stats: ConversionStats,
) -> None:
    if preview_count <= 0:
        return

    image_module, image_draw_module = load_pillow_modules()
    preview_dir = out_dir / "outputs" / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)

    selected_samples = sample_prepared_samples(samples=samples, limit=preview_count, seed=seed)
    for index, sample in enumerate(selected_samples, start=1):
        try:
            with image_module.open(sample.image_path) as image:
                width, height = image.size
                canvas = image.convert("RGB")

            draw = image_draw_module.Draw(canvas)
            x1, y1, x2, y2 = clamp_bbox(sample.annotation.bbox, width, height)
            draw.rectangle((x1, y1, x2, y2), outline="red", width=3)
            draw.polygon(sample.annotation.vertices, outline="yellow", width=2)
            draw.text((x1, max(0, y1 - 18)), sample.annotation.plate_text, fill="red")

            output_path = preview_dir / f"{index:03d}_{sample.image_path.name}"
            canvas.save(output_path)
            stats.preview_images_written += 1
        except (OSError, ValueError) as exc:
            stats.skipped_files += 1
            print(f"[prepare_ccpd] WARNING: skipped preview sample {sample.image_path.name}: {exc}")

    print(f"[prepare_ccpd] Preview: wrote {stats.preview_images_written} images to {preview_dir}")


def sample_prepared_samples(samples: Sequence[PreparedSample], limit: int, seed: int) -> List[PreparedSample]:
    if limit >= len(samples):
        return list(samples)

    sampled = list(samples)
    random.Random(seed).shuffle(sampled)
    return sampled[:limit]


def write_yolo_config(out_dir: Path) -> None:
    config_dir = out_dir / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "ccpd_yolo.yaml"
    content = "\n".join(
        [
            f"path: {out_dir.as_posix()}",
            "train: images/train",
            "val: images/val",
            "test: images/test",
            "",
            "names:",
            "  0: license_plate",
            "",
        ]
    )
    config_path.write_text(content, encoding="utf-8")
    print(f"[prepare_ccpd] Wrote YOLO config: {config_path}")


def print_dry_run_preview(samples: Sequence[PreparedSample]) -> None:
    print("[prepare_ccpd] First parsed samples:")
    for index, sample in enumerate(samples[:5], start=1):
        annotation = sample.annotation
        print(
            f"  {index}. file={sample.image_path.name} "
            f"plate={annotation.plate_text} "
            f"bbox={annotation.bbox} "
            f"tilt={annotation.tilt_degrees} "
            f"brightness={annotation.brightness} "
            f"blur={annotation.blurriness}"
        )
    if not samples:
        print("  (no valid CCPD filenames were parsed)")


def print_skipped_summary(skipped: Sequence[SkippedFile]) -> None:
    if not skipped:
        return

    print("[prepare_ccpd] Example skipped files:")
    for skipped_file in skipped[:5]:
        print(f"  - {skipped_file.image_path.name}: {skipped_file.reason}")


def print_stats(stats: ConversionStats) -> None:
    print("[prepare_ccpd] Summary:")
    print(f"  candidate_images={stats.candidate_images}")
    print(f"  selected_images={stats.selected_images}")
    print(f"  valid_samples={stats.valid_samples}")
    print(f"  skipped_files={stats.skipped_files}")
    print(
        "  split_counts="
        f"train:{stats.split_counts.get('train', 0)},"
        f" val:{stats.split_counts.get('val', 0)},"
        f" test:{stats.split_counts.get('test', 0)}"
    )
    print(f"  yolo_labels_written={stats.yolo_labels_written}")
    print(f"  crnn_crops_written={stats.crnn_crops_written}")
    print(f"  preview_images_written={stats.preview_images_written}")


def load_pillow_modules():
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise ImportError(
            "Pillow is required to prepare CCPD images. Please install it first, for example: pip install Pillow"
        ) from exc
    return Image, ImageDraw


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, NotADirectoryError, ValueError, ImportError) as exc:
        print(f"[prepare_ccpd] ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
