from django.contrib import admin

from .models import RecognitionRecord


@admin.register(RecognitionRecord)
class RecognitionRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "original_filename", "status", "plate_text", "yolo_confidence", "created_at")
    search_fields = ("original_filename", "plate_text", "status")
    list_filter = ("status", "created_at")
