from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict, List, Optional

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from inference.license_plate_pipeline import (
    DetectionPrediction,
    load_charset,
    load_crnn_model,
    load_yolo_model,
    process_single_image,
    resolve_devices,
)


_SERVICE_CACHE: Optional["LicensePlateRecognitionService"] = None


class LicensePlateRecognitionService:
    def __init__(self) -> None:
        self.yolo_weights = Path(settings.LPR_YOLO_WEIGHTS).resolve()
        self.crnn_weights = Path(settings.LPR_CRNN_WEIGHTS).resolve()
        self.charset_path = Path(settings.LPR_CHARSET).resolve()
        self.output_dir = Path(settings.LPR_OUTPUT_DIR).resolve()
        self.media_root = Path(settings.MEDIA_ROOT).resolve()
        self.conf_threshold = float(settings.LPR_CONFIDENCE)
        self.annotated_dir = self.output_dir / "annotated"
        self.crops_dir = self.output_dir / "crops"
        self.upload_dir = self.media_root / "uploads"

        self._yolo_model = None
        self._charset = None
        self._crnn_model = None
        self._crnn_config: Optional[Dict[str, object]] = None
        self._torch_device, self._yolo_device = resolve_devices(settings.LPR_DEVICE)

    def ensure_directories(self) -> None:
        self.media_root.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.annotated_dir.mkdir(parents=True, exist_ok=True)
        self.crops_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def model_paths_ready(self) -> bool:
        return self.yolo_weights.exists() and self.crnn_weights.exists() and self.charset_path.exists()

    def load_models(self) -> None:
        if self._yolo_model is not None and self._crnn_model is not None and self._charset is not None:
            return

        if not self.model_paths_ready():
            raise FileNotFoundError(
                "模型文件不存在，请检查 LPR_YOLO_WEIGHTS、LPR_CRNN_WEIGHTS、LPR_CHARSET 配置。"
            )

        self.ensure_directories()
        self._yolo_model = load_yolo_model(self.yolo_weights)
        self._charset = load_charset(self.charset_path)
        self._crnn_model, self._crnn_config = load_crnn_model(
            checkpoint_path=self.crnn_weights,
            charset=self._charset,
            device=self._torch_device,
            img_height=32,
            img_width=160,
        )

    def is_model_ready(self) -> bool:
        try:
            self.load_models()
        except Exception:
            return False
        return True

    def save_upload_file(self, uploaded_file: UploadedFile) -> Path:
        self.ensure_directories()
        safe_name = Path(uploaded_file.name).name
        unique_name = f"{uuid.uuid4().hex}_{safe_name}"
        destination = self.upload_dir / unique_name
        with destination.open("wb") as handle:
            for chunk in uploaded_file.chunks():
                handle.write(chunk)
        return destination

    def recognize_image(self, image_path: str | Path) -> Dict[str, object]:
        self.load_models()
        assert self._yolo_model is not None
        assert self._crnn_model is not None
        assert self._charset is not None
        assert self._crnn_config is not None

        source_path = Path(image_path).resolve()
        predictions = process_single_image(
            image_path=source_path,
            image_rel_path=source_path.name,
            source_root=source_path,
            yolo_model=self._yolo_model,
            yolo_device=self._yolo_device,
            conf_threshold=self.conf_threshold,
            crnn_model=self._crnn_model,
            charset=self._charset,
            crnn_device=self._torch_device,
            img_height=int(self._crnn_config["img_height"]),
            img_width=int(self._crnn_config["img_width"]),
            grayscale=bool(self._crnn_config["grayscale"]),
            annotated_dir=self.annotated_dir,
            crops_dir=self.crops_dir,
        )
        return self.build_response(source_path, predictions)

    def build_response(self, image_path: Path, predictions: List[DetectionPrediction]) -> Dict[str, object]:
        ok_predictions = [item for item in predictions if item.status == "ok"]
        if ok_predictions:
            best = max(ok_predictions, key=lambda item: item.yolo_confidence)
            return {
                "status": "ok",
                "plate_text": best.plate_text,
                "bbox": [best.bbox_x1, best.bbox_y1, best.bbox_x2, best.bbox_y2],
                "yolo_confidence": best.yolo_confidence,
                "annotated_image_path": best.annotated_image_path,
                "crop_image_path": best.crop_path,
                "detections": [self.serialize_prediction(item) for item in ok_predictions],
                "image_path": str(image_path),
            }

        no_detection = next((item for item in predictions if item.status == "no_detection"), None)
        if no_detection is not None:
            return {
                "status": "no_detection",
                "message": "未检测到车牌",
                "annotated_image_path": no_detection.annotated_image_path,
                "image_path": str(image_path),
            }

        first_error = predictions[0] if predictions else None
        return {
            "status": "error",
            "message": first_error.error_message if first_error else "识别失败",
            "annotated_image_path": first_error.annotated_image_path if first_error else "",
            "crop_image_path": first_error.crop_path if first_error else "",
            "image_path": str(image_path),
        }

    @staticmethod
    def serialize_prediction(prediction: DetectionPrediction) -> Dict[str, object]:
        return {
            "status": prediction.status,
            "plate_text": prediction.plate_text,
            "bbox": [prediction.bbox_x1, prediction.bbox_y1, prediction.bbox_x2, prediction.bbox_y2],
            "yolo_confidence": prediction.yolo_confidence,
            "crop_image_path": prediction.crop_path,
            "annotated_image_path": prediction.annotated_image_path,
            "error_message": prediction.error_message,
        }


def get_service() -> LicensePlateRecognitionService:
    global _SERVICE_CACHE
    if _SERVICE_CACHE is None:
        _SERVICE_CACHE = LicensePlateRecognitionService()
    return _SERVICE_CACHE
