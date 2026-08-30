from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    total_servers = serializers.IntegerField()
    online_servers = serializers.IntegerField()
    offline_servers = serializers.IntegerField()
    total_firewalls = serializers.IntegerField()
    pending_approvals = serializers.IntegerField()
    active_users = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    generated_at = serializers.CharField()


class MetricPointSerializer(serializers.Serializer):
    timestamp = serializers.CharField()
    value = serializers.FloatField()


class SecurityTimelinePointSerializer(serializers.Serializer):
    date = serializers.CharField()
    count = serializers.IntegerField()


class SecurityTypePointSerializer(serializers.Serializer):
    event_type = serializers.CharField()
    count = serializers.IntegerField()


class AlertTrendPointSerializer(serializers.Serializer):
    date = serializers.CharField()
    critical = serializers.IntegerField()
    high = serializers.IntegerField()
    medium = serializers.IntegerField()
    low = serializers.IntegerField()
