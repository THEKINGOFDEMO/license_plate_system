from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.db.models import Q
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RecognitionRecord
from .serializers import RecognitionRecordSerializer, RecognizeUploadSerializer
from .services import get_service


class HealthAPIView(APIView):
    def get(self, request):
        service = get_service()
        return Response({"status": "ok", "model_ready": service.is_model_ready()})


class StatsAPIView(APIView):
    def get(self, request):
        queryset = RecognitionRecord.objects.all()
        return Response(
            {
                "status": "ok",
                "total": queryset.count(),
                "ok": queryset.filter(status="ok").count(),
                "no_detection": queryset.filter(status="no_detection").count(),
                "error": queryset.filter(status="error").count(),
            }
        )


class RecognizeAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = RecognizeUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data["image"]
        service = get_service()

        try:
            saved_image_path = service.save_upload_file(uploaded_file)
            result = service.recognize_image(saved_image_path)
        except FileNotFoundError as exc:
            return Response({"status": "error", "message": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as exc:  # pragma: no cover - runtime safety
            return Response({"status": "error", "message": f"识别失败: {exc}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        record = RecognitionRecord.objects.create(
            original_filename=uploaded_file.name,
            upload_image_path=str(saved_image_path),
            status=str(result.get("status", "error")),
            plate_text=str(result.get("plate_text", "")),
            bbox=result.get("bbox", []),
            yolo_confidence=result.get("yolo_confidence"),
            annotated_image_path=str(result.get("annotated_image_path", "")),
            crop_image_path=str(result.get("crop_image_path", "")),
            raw_result=result,
        )

        payload = dict(result)
        if payload.get("status") == "ok":
            payload["annotated_image_url"] = build_media_url(request, payload.get("annotated_image_path", ""))
            payload["crop_image_url"] = build_media_url(request, payload.get("crop_image_path", ""))
            payload["record_id"] = record.id
        elif payload.get("status") == "no_detection":
            payload["record_id"] = record.id
        else:
            payload["record_id"] = record.id

        return Response(payload)


class RecognitionRecordListAPIView(APIView):
    def get(self, request):
        queryset = RecognitionRecord.objects.all()

        status_filter = (request.query_params.get("status") or "").strip()
        keyword = (request.query_params.get("keyword") or "").strip()
        page = parse_positive_int(request.query_params.get("page"), default=1)
        page_size = parse_positive_int(request.query_params.get("page_size"), default=10)
        page_size = min(page_size, 100)

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if keyword:
            queryset = queryset.filter(Q(original_filename__icontains=keyword) | Q(plate_text__icontains=keyword))

        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        records = list(queryset[start:end])
        serializer = RecognitionRecordSerializer(records, many=True, context={"request": request})
        payload = {
            "status": "ok",
            "count": total_count,
            "page": page,
            "page_size": page_size,
            "results": serializer.data,
            "records": serializer.data,
        }
        return Response(payload)


def build_media_url(request, file_path: str) -> str:
    if not file_path:
        return ""

    media_root = Path(settings.MEDIA_ROOT).resolve()
    candidate = Path(file_path).resolve()
    try:
        relative_path = candidate.relative_to(media_root)
    except ValueError:
        return ""
    return request.build_absolute_uri(f"{settings.MEDIA_URL}{relative_path.as_posix()}")


def parse_positive_int(raw_value, default: int) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default
