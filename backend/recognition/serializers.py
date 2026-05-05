from __future__ import annotations

from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from .models import RecognitionRecord


class RecognizeUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)


class RecognitionRecordSerializer(serializers.ModelSerializer):
    record_id = serializers.IntegerField(source="id", read_only=True)
    annotated_image_url = serializers.SerializerMethodField()
    crop_image_url = serializers.SerializerMethodField()

    class Meta:
        model = RecognitionRecord
        fields = [
            "id",
            "record_id",
            "original_filename",
            "upload_image_path",
            "status",
            "plate_text",
            "bbox",
            "yolo_confidence",
            "annotated_image_path",
            "crop_image_path",
            "annotated_image_url",
            "crop_image_url",
            "raw_result",
            "created_at",
        ]

    def get_annotated_image_url(self, obj: RecognitionRecord) -> str:
        return self._build_media_url(obj.annotated_image_path)

    def get_crop_image_url(self, obj: RecognitionRecord) -> str:
        return self._build_media_url(obj.crop_image_path)

    def _build_media_url(self, file_path: str) -> str:
        if not file_path:
            return ""
        request = self.context.get("request")
        media_root = Path(settings.MEDIA_ROOT).resolve()
        candidate = Path(file_path).resolve()
        try:
            relative_path = candidate.relative_to(media_root)
        except ValueError:
            return ""
        relative_url = f"{settings.MEDIA_URL}{relative_path.as_posix()}"
        return request.build_absolute_uri(relative_url) if request else relative_url
