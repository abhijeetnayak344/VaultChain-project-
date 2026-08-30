import uuid

from django.db import models

from apps.compute.models import Server


class Alert(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    source = models.CharField(max_length=64, default="system")
    severity = models.CharField(max_length=16, choices=Severity.choices, db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True)
    occurred_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "monitoring_alert"
        ordering = ["-occurred_at"]

    def __str__(self):
        return self.title


class SecurityEvent(models.Model):
    class EventType(models.TextChoices):
        INTRUSION = "intrusion", "Intrusion"
        MALWARE = "malware", "Malware"
        POLICY = "policy_violation", "Policy violation"
        BRUTE_FORCE = "brute_force", "Brute force"
        ANOMALY = "anomaly", "Anomaly"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=32, choices=EventType.choices, db_index=True)
    severity = models.CharField(max_length=16, default="medium")
    message = models.CharField(max_length=255)
    occurred_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "monitoring_security_event"
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.event_type} @ {self.occurred_at}"


class ResourceMetric(models.Model):
    class Metric(models.TextChoices):
        CPU = "cpu", "CPU"
        RAM = "ram", "RAM"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric = models.CharField(max_length=8, choices=Metric.choices, db_index=True)
    value = models.DecimalField(max_digits=5, decimal_places=2)
    recorded_at = models.DateTimeField(db_index=True)
    server = models.ForeignKey(Server, null=True, blank=True, on_delete=models.SET_NULL, related_name="metrics")

    class Meta:
        db_table = "monitoring_resource_metric"
        ordering = ["recorded_at"]
        indexes = [
            models.Index(fields=["metric", "recorded_at"]),
        ]
