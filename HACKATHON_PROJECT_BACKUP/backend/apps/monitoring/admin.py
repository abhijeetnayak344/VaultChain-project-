from django.contrib import admin

from apps.monitoring.models import Alert, ResourceMetric, SecurityEvent


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("title", "severity", "status", "occurred_at")
    list_filter = ("severity", "status")


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "severity", "occurred_at")
    list_filter = ("event_type", "severity")


@admin.register(ResourceMetric)
class ResourceMetricAdmin(admin.ModelAdmin):
    list_display = ("metric", "value", "recorded_at", "server")
    list_filter = ("metric",)
