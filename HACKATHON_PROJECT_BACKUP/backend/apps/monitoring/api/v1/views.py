from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import require_permission
from apps.monitoring import services
from apps.monitoring.api.serializers import (
    AlertTrendPointSerializer,
    DashboardSummarySerializer,
    MetricPointSerializer,
    SecurityTimelinePointSerializer,
    SecurityTypePointSerializer,
)


class DashboardPermissionMixin:
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [IsAuthenticated(), require_permission("dashboard:read")()]


class DashboardSummaryView(DashboardPermissionMixin, APIView):
    def get(self, request):
        serializer = DashboardSummarySerializer(data=services.dashboard_summary())
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class CpuUsageView(DashboardPermissionMixin, APIView):
    def get(self, request):
        hours = int(request.query_params.get("hours", 24))
        hours = max(1, min(hours, 168))
        serializer = MetricPointSerializer(data=services.cpu_usage_series(hours), many=True)
        serializer.is_valid(raise_exception=True)
        return Response({"metric": "cpu", "series": serializer.data})


class RamUsageView(DashboardPermissionMixin, APIView):
    def get(self, request):
        hours = int(request.query_params.get("hours", 24))
        hours = max(1, min(hours, 168))
        serializer = MetricPointSerializer(data=services.ram_usage_series(hours), many=True)
        serializer.is_valid(raise_exception=True)
        return Response({"metric": "ram", "series": serializer.data})


class SecurityEventsChartView(DashboardPermissionMixin, APIView):
    def get(self, request):
        days = int(request.query_params.get("days", 7))
        days = max(1, min(days, 90))
        payload = services.security_event_series(days)
        timeline = SecurityTimelinePointSerializer(data=payload["timeline"], many=True)
        by_type = SecurityTypePointSerializer(data=payload["by_type"], many=True)
        timeline.is_valid(raise_exception=True)
        by_type.is_valid(raise_exception=True)
        return Response({"timeline": timeline.data, "by_type": by_type.data})


class AlertTrendsView(DashboardPermissionMixin, APIView):
    def get(self, request):
        days = int(request.query_params.get("days", 14))
        days = max(1, min(days, 90))
        serializer = AlertTrendPointSerializer(data=services.alert_trend_series(days), many=True)
        serializer.is_valid(raise_exception=True)
        return Response({"series": serializer.data})
