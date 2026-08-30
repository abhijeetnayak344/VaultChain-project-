from django.urls import path

from apps.monitoring.api.v1.views import (
    AlertTrendsView,
    CpuUsageView,
    DashboardSummaryView,
    RamUsageView,
    SecurityEventsChartView,
)

urlpatterns = [
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("dashboard/charts/cpu/", CpuUsageView.as_view(), name="dashboard-cpu"),
    path("dashboard/charts/ram/", RamUsageView.as_view(), name="dashboard-ram"),
    path("dashboard/charts/security-events/", SecurityEventsChartView.as_view(), name="dashboard-security-events"),
    path("dashboard/charts/alerts/", AlertTrendsView.as_view(), name="dashboard-alert-trends"),
]
