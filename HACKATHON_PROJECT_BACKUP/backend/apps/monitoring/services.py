from datetime import timedelta

from django.db.models import Avg, Count
from django.db.models.functions import TruncDay, TruncHour
from django.utils import timezone

from apps.accounts.models import User
from apps.compute.models import Server
from apps.monitoring.models import Alert, ResourceMetric, SecurityEvent
from apps.network.models import Firewall
from apps.network.services import pending_approval_count


def raise_alert(*, title, source="system", severity="critical"):
    return Alert.objects.create(
        title=title[:255],
        source=(source or "system")[:64],
        severity=severity,
        status=Alert.Status.OPEN,
        occurred_at=timezone.now(),
    )


def dashboard_summary():
    now = timezone.now()
    active_since = now - timedelta(hours=24)
    return {
        "total_servers": Server.objects.count(),
        "online_servers": Server.objects.filter(status=Server.Status.ONLINE).count(),
        "offline_servers": Server.objects.filter(status=Server.Status.OFFLINE).count(),
        "total_firewalls": Firewall.objects.count(),
        "pending_approvals": pending_approval_count(),
        "active_users": User.objects.filter(is_active=True, last_login__gte=active_since).count(),
        "critical_alerts": Alert.objects.filter(
            severity=Alert.Severity.CRITICAL,
            status=Alert.Status.OPEN,
        ).count(),
        "generated_at": now.isoformat(),
    }


def _metric_series(metric, hours=24):
    since = timezone.now() - timedelta(hours=hours)
    rows = (
        ResourceMetric.objects.filter(metric=metric, recorded_at__gte=since)
        .annotate(bucket=TruncHour("recorded_at"))
        .values("bucket")
        .annotate(value=Avg("value"))
        .order_by("bucket")
    )
    return [{"timestamp": row["bucket"].isoformat(), "value": round(float(row["value"]), 2)} for row in rows]


def cpu_usage_series(hours=24):
    return _metric_series(ResourceMetric.Metric.CPU, hours=hours)


def ram_usage_series(hours=24):
    return _metric_series(ResourceMetric.Metric.RAM, hours=hours)


def security_event_series(days=7):
    since = timezone.now() - timedelta(days=days)
    by_day = (
        SecurityEvent.objects.filter(occurred_at__gte=since)
        .annotate(bucket=TruncDay("occurred_at"))
        .values("bucket")
        .annotate(count=Count("id"))
        .order_by("bucket")
    )
    by_type = (
        SecurityEvent.objects.filter(occurred_at__gte=since)
        .values("event_type")
        .annotate(count=Count("id"))
        .order_by("event_type")
    )
    return {
        "timeline": [{"date": row["bucket"].date().isoformat(), "count": row["count"]} for row in by_day],
        "by_type": [{"event_type": row["event_type"], "count": row["count"]} for row in by_type],
    }


def alert_trend_series(days=14):
    since = timezone.now() - timedelta(days=days)
    rows = (
        Alert.objects.filter(occurred_at__gte=since)
        .annotate(bucket=TruncDay("occurred_at"))
        .values("bucket", "severity")
        .annotate(count=Count("id"))
        .order_by("bucket")
    )
    by_date = {}
    for row in rows:
        key = row["bucket"].date().isoformat()
        by_date.setdefault(key, {"date": key, "critical": 0, "high": 0, "medium": 0, "low": 0})
        by_date[key][row["severity"]] = row["count"]
    return list(by_date.values())
