from django.urls import path

from .views import HealthAPIView, RecognitionRecordListAPIView, RecognizeAPIView, StatsAPIView


urlpatterns = [
    path("health/", HealthAPIView.as_view(), name="api-health"),
    path("stats/", StatsAPIView.as_view(), name="api-stats"),
    path("recognize/", RecognizeAPIView.as_view(), name="api-recognize"),
    path("records/", RecognitionRecordListAPIView.as_view(), name="api-records"),
]
