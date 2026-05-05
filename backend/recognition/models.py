from __future__ import annotations

from django.db import models


class RecognitionRecord(models.Model):
    original_filename = models.CharField(max_length=255)
    upload_image_path = models.CharField(max_length=1024)
    status = models.CharField(max_length=32)
    plate_text = models.CharField(max_length=64, blank=True)
    bbox = models.JSONField(default=list, blank=True)
    yolo_confidence = models.FloatField(null=True, blank=True)
    annotated_image_path = models.CharField(max_length=1024, blank=True)
    crop_image_path = models.CharField(max_length=1024, blank=True)
    raw_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.original_filename} - {self.status}"
