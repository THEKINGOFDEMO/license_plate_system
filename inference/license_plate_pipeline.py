"""YOLO + CRNN inference pipeline for license plate detection and recognition."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont

try:
    from train.crnn_dataset import CRNNCharset
    from train.crnn_model import CRNN
except ImportError:
    from crnn_dataset import CRNNCharset
    from crnn_model import CRNN


DEFAULT_YOLO_WEIGHTS = "/cloud/cloud-ssd1/models/yolo/yolov8n_ccpd10000_best.pt"
DEFAULT_CRNN_WEIGHTS = "/cloud/cloud-ssd1/models/crnn/crnn_ccpd10000_best.pth"
DEFAULT_CHARSET = "/cloud/cloud-ssd1/models/crnn/charset.json"
DEFAULT_SOURCE = "/cloud/cloud-ssd1/lpr_data/ccpd_10000/images/test"
DEFAULT_OUTPUT_DIR = "/cloud/cloud-ssd1/runs/pipeline/ccpd10000_yolo_crnn_predict"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass
class DetectionPrediction:
    image_path: str
    image_rel_path: str
    status: str
    detection_index: int
    bbox_x1: int
    bbox_y1: int
    bbox_x2: int
    bbox_y2: int
    yolo_confidence: float
    plate_text: str
    crop_path: str
    annotated_image_path: str
    error_message: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run YOLO + CRNN pipeline inference on one image or a directory.")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Single image path or directory path.")
    parser.add_argument("--yolo-weights", default=DEFAULT_YOLO_WEIGHTS, help="YOLO checkpoint path.")
    parser.add_argument("--crnn-weights", default=DEFAULT_CRNN_WEIGHTS, help="CRNN checkpoint path.")
    parser.add_argument("--charset", default=DEFAULT_CHARSET, help="CRNN charset.json path.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory used to save CSV and annotated images.")
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold.")
    parser.add_argument("--device", default="cuda:0", help="Inference device, for example cuda:0 or cpu.")
    parser.add_argument("--img-height", type=int, default=32, help="CRNN input image height.")
    parser.add_argument("--img-width", type=int, default=160, help="CRNN input image width.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    source_path = Path(args.source).resolve()
    yolo_weights = Path(args.yolo_weights).resolve()
    crnn_weights = Path(args.crnn_weights).resolve()
    charset_path = Path(args.charset).resolve()
    output_dir = Path(args.output_dir).resolve()

    validate_path_exists(source_path, "source")
    validate_path_exists(yolo_weights, "YOLO weights")
    validate_path_exists(crnn_weights, "CRNN weights")
    validate_path_exists(charset_path, "charset")

    image_paths = collect_image_paths(source_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir = output_dir / "annotated"
    crops_dir = output_dir / "crops"
    annotated_dir.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)

    torch_device, yolo_device = resolve_devices(args.device)
    print(f"[pipeline] Found {len(image_paths)} image(s) under: {source_path}")
    print(f"[pipeline] YOLO weights: {yolo_weights}")
    print(f"[pipeline] CRNN weights: {crnn_weights}")
    print(f"[pipeline] Charset: {charset_path}")
    print(f"[pipeline] Output directory: {output_dir}")

    yolo_model = load_yolo_model(yolo_weights)
    charset = load_charset(charset_path)
    crnn_model, crnn_config = load_crnn_model(
        checkpoint_path=crnn_weights,
        charset=charset,
        device=torch_device,
        img_height=args.img_height,
        img_width=args.img_width,
    )

    predictions: List[DetectionPrediction] = []
    success_count = 0
    no_detection_count = 0
    error_count = 0

    for index, image_path in enumerate(image_paths, start=1):
        image_rel_path = build_relative_image_path(source_path, image_path)
        print(f"[pipeline] [{index}/{len(image_paths)}] Processing: {image_rel_path}")
        try:
            image_predictions = process_single_image(
                image_path=image_path,
                image_rel_path=image_rel_path,
                source_root=source_path,
                yolo_model=yolo_model,
                yolo_device=yolo_device,
                conf_threshold=args.conf,
                crnn_model=crnn_model,
                charset=charset,
                crnn_device=torch_device,
                img_height=int(crnn_config["img_height"]),
                img_width=int(crnn_config["img_width"]),
                grayscale=bool(crnn_config["grayscale"]),
                annotated_dir=annotated_dir,
                crops_dir=crops_dir,
            )
            predictions.extend(image_predictions)
            if any(item.status == "ok" for item in image_predictions):
                success_count += 1
            elif any(item.status == "no_detection" for item in image_predictions):
                no_detection_count += 1
            else:
                error_count += 1
        except Exception as exc:  # pragma: no cover - defensive runtime path
            error_count += 1
            annotated_path = annotated_dir / image_path.name
            predictions.append(
                DetectionPrediction(
                    image_path=str(image_path),
                    image_rel_path=image_rel_path,
                    status="error",
                    detection_index=-1,
                    bbox_x1=-1,
                    bbox_y1=-1,
                    bbox_x2=-1,
                    bbox_y2=-1,
                    yolo_confidence=0.0,
                    plate_text="",
                    crop_path="",
                    annotated_image_path=str(annotated_path),
                    error_message=str(exc),
                )
            )
            print(f"[pipeline] ERROR: {image_rel_path}: {exc}")

    predictions_csv_path = output_dir / "predictions.csv"
    save_predictions_csv(predictions, predictions_csv_path)
    print(f"[pipeline] Saved predictions CSV: {predictions_csv_path}")
    print(
        "[pipeline] Summary: "
        f"images={len(image_paths)} success={success_count} "
        f"no_detection={no_detection_count} error={error_count}"
    )
    return 0


def validate_path_exists(path: Path, path_label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{path_label} does not exist: {path}")


def collect_image_paths(source_path: Path) -> List[Path]:
    if source_path.is_file():
        return [source_path]
    if source_path.is_dir():
        image_paths = sorted(path for path in source_path.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES)
        if not image_paths:
            raise FileNotFoundError(f"No supported image files found under directory: {source_path}")
        return image_paths
    raise FileNotFoundError(f"Source path does not exist: {source_path}")


def build_relative_image_path(source_root: Path, image_path: Path) -> str:
    if source_root.is_file():
        return image_path.name
    return str(image_path.relative_to(source_root))


def resolve_devices(device_argument: str) -> Tuple[torch.device, str]:
    if device_argument != "cpu" and not torch.cuda.is_available():
        print(f"[pipeline] CUDA is unavailable, falling back from '{device_argument}' to 'cpu'.")
        return torch.device("cpu"), "cpu"
    return torch.device(device_argument), device_argument


def load_yolo_model(yolo_weights: Path):
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - dependency error
        raise ImportError("ultralytics is required for pipeline inference. Please run 'pip install -r requirements.txt'.") from exc
    return YOLO(str(yolo_weights))


def load_charset(charset_path: Path) -> CRNNCharset:
    payload = json.loads(charset_path.read_text(encoding="utf-8"))
    if "characters" not in payload:
        raise ValueError(f"Invalid charset.json, missing 'characters': {charset_path}")
    return CRNNCharset(payload["characters"])


def load_crnn_model(
    checkpoint_path: Path,
    charset: CRNNCharset,
    device: torch.device,
    img_height: int,
    img_width: int,
) -> Tuple[CRNN, Dict[str, object]]:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    checkpoint_state = checkpoint.get("model_state_dict", checkpoint)
    grayscale = bool(checkpoint.get("grayscale", True))
    checkpoint_img_height = int(checkpoint.get("img_height", img_height))
    checkpoint_img_width = int(checkpoint.get("img_width", img_width))

    model = CRNN(
        img_height=checkpoint_img_height,
        img_width=checkpoint_img_width,
        num_channels=1 if grayscale else 3,
        num_classes=charset.num_classes,
    ).to(device)
    model.load_state_dict(checkpoint_state)
    model.eval()
    return model, {"grayscale": grayscale, "img_height": checkpoint_img_height, "img_width": checkpoint_img_width}


def process_single_image(
    image_path: Path,
    image_rel_path: str,
    source_root: Path,
    yolo_model,
    yolo_device: str,
    conf_threshold: float,
    crnn_model: CRNN,
    charset: CRNNCharset,
    crnn_device: torch.device,
    img_height: int,
    img_width: int,
    grayscale: bool,
    annotated_dir: Path,
    crops_dir: Path,
) -> List[DetectionPrediction]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Failed to read image: {image_path}")

    annotated_image = image.copy()
    annotated_output_path = build_output_image_path(annotated_dir, source_root, image_path)
    annotated_output_path.parent.mkdir(parents=True, exist_ok=True)

    results = yolo_model.predict(source=str(image_path), conf=conf_threshold, device=yolo_device, verbose=False)
    if not results:
        add_status_banner(annotated_image, "NO_PLATE")
        cv2.imwrite(str(annotated_output_path), annotated_image)
        return [
            DetectionPrediction(
                image_path=str(image_path),
                image_rel_path=image_rel_path,
                status="no_detection",
                detection_index=-1,
                bbox_x1=-1,
                bbox_y1=-1,
                bbox_x2=-1,
                bbox_y2=-1,
                yolo_confidence=0.0,
                plate_text="",
                crop_path="",
                annotated_image_path=str(annotated_output_path),
                error_message="YOLO returned no results.",
            )
        ]

    boxes = results[0].boxes
    if boxes is None or boxes.xyxy is None or len(boxes) == 0:
        add_status_banner(annotated_image, "NO_PLATE")
        cv2.imwrite(str(annotated_output_path), annotated_image)
        return [
            DetectionPrediction(
                image_path=str(image_path),
                image_rel_path=image_rel_path,
                status="no_detection",
                detection_index=-1,
                bbox_x1=-1,
                bbox_y1=-1,
                bbox_x2=-1,
                bbox_y2=-1,
                yolo_confidence=0.0,
                plate_text="",
                crop_path="",
                annotated_image_path=str(annotated_output_path),
                error_message="No plate detected above confidence threshold.",
            )
        ]

    xyxy = boxes.xyxy.detach().cpu().numpy()
    confidences = boxes.conf.detach().cpu().numpy() if boxes.conf is not None else np.zeros(len(xyxy), dtype=np.float32)
    predictions: List[DetectionPrediction] = []

    for detection_index, (coords, confidence) in enumerate(zip(xyxy, confidences), start=1):
        x1, y1, x2, y2 = sanitize_bbox(coords, image.shape)
        crop = image[y1:y2, x1:x2]
        crop_output_path = build_crop_output_path(crops_dir, source_root, image_path, detection_index)
        crop_output_path.parent.mkdir(parents=True, exist_ok=True)

        if crop.size == 0:
            predictions.append(
                DetectionPrediction(
                    image_path=str(image_path),
                    image_rel_path=image_rel_path,
                    status="crop_error",
                    detection_index=detection_index,
                    bbox_x1=x1,
                    bbox_y1=y1,
                    bbox_x2=x2,
                    bbox_y2=y2,
                    yolo_confidence=float(confidence),
                    plate_text="",
                    crop_path=str(crop_output_path),
                    annotated_image_path=str(annotated_output_path),
                    error_message="Detected bbox produced an empty crop.",
                )
            )
            continue

        cv2.imwrite(str(crop_output_path), crop)

        try:
            plate_text = predict_plate_text(
                crop_bgr=crop,
                model=crnn_model,
                charset=charset,
                device=crnn_device,
                img_height=img_height,
                img_width=img_width,
                grayscale=grayscale,
            )
            status = "ok"
            error_message = ""
        except Exception as exc:  # pragma: no cover - defensive runtime path
            plate_text = ""
            status = "crnn_error"
            error_message = str(exc)

        draw_detection(
            annotated_image=annotated_image,
            bbox=(x1, y1, x2, y2),
            confidence=float(confidence),
            plate_text=plate_text or status.upper(),
        )
        predictions.append(
            DetectionPrediction(
                image_path=str(image_path),
                image_rel_path=image_rel_path,
                status=status,
                detection_index=detection_index,
                bbox_x1=x1,
                bbox_y1=y1,
                bbox_x2=x2,
                bbox_y2=y2,
                yolo_confidence=float(confidence),
                plate_text=plate_text,
                crop_path=str(crop_output_path),
                annotated_image_path=str(annotated_output_path),
                error_message=error_message,
            )
        )

    cv2.imwrite(str(annotated_output_path), annotated_image)
    return predictions


def build_output_image_path(output_root: Path, source_root: Path, image_path: Path) -> Path:
    relative_path = Path(build_relative_image_path(source_root, image_path))
    return output_root / relative_path


def build_crop_output_path(output_root: Path, source_root: Path, image_path: Path, detection_index: int) -> Path:
    relative_path = Path(build_relative_image_path(source_root, image_path))
    return output_root / relative_path.parent / f"{relative_path.stem}_plate_{detection_index}{relative_path.suffix}"


def sanitize_bbox(coords: Sequence[float], image_shape: Sequence[int]) -> Tuple[int, int, int, int]:
    height, width = int(image_shape[0]), int(image_shape[1])
    x1, y1, x2, y2 = [int(round(float(value))) for value in coords]
    x1 = max(0, min(x1, width - 1))
    y1 = max(0, min(y1, height - 1))
    x2 = max(x1 + 1, min(x2, width))
    y2 = max(y1 + 1, min(y2, height))
    return x1, y1, x2, y2


@torch.no_grad()
def predict_plate_text(
    crop_bgr: np.ndarray,
    model: CRNN,
    charset: CRNNCharset,
    device: torch.device,
    img_height: int,
    img_width: int,
    grayscale: bool,
) -> str:
    if grayscale:
        crop = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
        crop = cv2.resize(crop, (img_width, img_height), interpolation=cv2.INTER_LINEAR)
        array = crop.astype(np.float32) / 255.0
        array = np.expand_dims(array, axis=0)
    else:
        crop = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        crop = cv2.resize(crop, (img_width, img_height), interpolation=cv2.INTER_LINEAR)
        array = crop.astype(np.float32) / 255.0
        array = np.transpose(array, (2, 0, 1))

    image_tensor = torch.from_numpy(array).unsqueeze(0).to(device)
    logits = model(image_tensor)
    indices = logits.argmax(dim=2).squeeze(1).detach().cpu().tolist()
    return charset.decode_indices(indices)


def draw_detection(
    annotated_image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    confidence: float,
    plate_text: str,
) -> None:
    x1, y1, x2, y2 = bbox
    cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    label = f"{plate_text} | {confidence:.2f}"
    draw_unicode_label(annotated_image, label=label, x=x1, y=y1)


def add_status_banner(image: np.ndarray, text: str) -> None:
    cv2.putText(
        image,
        text,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 0, 255),
        2,
        cv2.LINE_AA,
    )


def draw_unicode_label(image_bgr: np.ndarray, label: str, x: int, y: int) -> None:
    font = load_annotation_font()
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    canvas = Image.fromarray(image_rgb)
    draw = ImageDraw.Draw(canvas)
    text_bbox = draw.textbbox((0, 0), label, font=font)
    text_width = int(text_bbox[2] - text_bbox[0])
    text_height = int(text_bbox[3] - text_bbox[1])
    label_y = max(0, y - text_height - 8)
    label_x2 = min(canvas.width, x + text_width + 10)
    label_y2 = min(canvas.height, label_y + text_height + 8)
    draw.rectangle([(x, label_y), (label_x2, label_y2)], fill=(0, 120, 0))
    draw.text((x + 5, label_y + 3), label, font=font, fill=(255, 255, 255))
    image_bgr[:, :, :] = cv2.cvtColor(np.asarray(canvas), cv2.COLOR_RGB2BGR)


def load_annotation_font() -> ImageFont.ImageFont:
    font_candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for font_path in font_candidates:
        path = Path(font_path)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=20)
            except OSError:
                continue
    return ImageFont.load_default()


def save_predictions_csv(predictions: Iterable[DetectionPrediction], output_path: Path) -> None:
    rows = [prediction.__dict__ for prediction in predictions]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_path",
                "image_rel_path",
                "status",
                "detection_index",
                "bbox_x1",
                "bbox_y1",
                "bbox_x2",
                "bbox_y2",
                "yolo_confidence",
                "plate_text",
                "crop_path",
                "annotated_image_path",
                "error_message",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
