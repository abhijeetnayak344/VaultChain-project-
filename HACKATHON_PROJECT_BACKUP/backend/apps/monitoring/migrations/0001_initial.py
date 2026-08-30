# Generated for monitoring alerts, events, and metrics.

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("compute", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Alert",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("source", models.CharField(default="system", max_length=64)),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("critical", "Critical"),
                            ("high", "High"),
                            ("medium", "Medium"),
                            ("low", "Low"),
                        ],
                        db_index=True,
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("acknowledged", "Acknowledged"),
                            ("resolved", "Resolved"),
                        ],
                        db_index=True,
                        default="open",
                        max_length=16,
                    ),
                ),
                ("occurred_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "monitoring_alert",
                "ordering": ["-occurred_at"],
            },
        ),
        migrations.CreateModel(
            name="SecurityEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("intrusion", "Intrusion"),
                            ("malware", "Malware"),
                            ("policy_violation", "Policy violation"),
                            ("brute_force", "Brute force"),
                            ("anomaly", "Anomaly"),
                        ],
                        db_index=True,
                        max_length=32,
                    ),
                ),
                ("severity", models.CharField(default="medium", max_length=16)),
                ("message", models.CharField(max_length=255)),
                ("occurred_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "monitoring_security_event",
                "ordering": ["-occurred_at"],
            },
        ),
        migrations.CreateModel(
            name="ResourceMetric",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "metric",
                    models.CharField(choices=[("cpu", "CPU"), ("ram", "RAM")], db_index=True, max_length=8),
                ),
                ("value", models.DecimalField(decimal_places=2, max_digits=5)),
                ("recorded_at", models.DateTimeField(db_index=True)),
                (
                    "server",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="metrics",
                        to="compute.server",
                    ),
                ),
            ],
            options={
                "db_table": "monitoring_resource_metric",
                "ordering": ["recorded_at"],
            },
        ),
        migrations.AddIndex(
            model_name="resourcemetric",
            index=models.Index(fields=["metric", "recorded_at"], name="monitoring__metric_recorded_idx"),
        ),
    ]
