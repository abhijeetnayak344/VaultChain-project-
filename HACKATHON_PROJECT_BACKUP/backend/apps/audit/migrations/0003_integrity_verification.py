# Verification status plus integrity check / security alert tables.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_auditlog_chain_anchor"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="verification_status",
            field=models.CharField(db_index=True, default="unverified", max_length=16),
        ),
        migrations.CreateModel(
            name="IntegrityCheck",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("current_hash", models.CharField(max_length=64)),
                ("blockchain_hash", models.CharField(blank=True, max_length=64)),
                ("stored_hash", models.CharField(blank=True, max_length=64)),
                ("chain_tx_id", models.CharField(blank=True, max_length=128)),
                ("result", models.CharField(choices=[("verified", "Verified"), ("alert", "Security alert"), ("not_anchored", "Not anchored"), ("unavailable", "Fabric unavailable")], db_index=True, max_length=16)),
                ("reason", models.CharField(blank=True, max_length=64)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                (
                    "audit_log",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="integrity_checks",
                        to="audit.auditlog",
                    ),
                ),
            ],
            options={
                "db_table": "audit_integrity_check",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="IntegrityAlert",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("local_hash", models.CharField(max_length=64)),
                ("chain_hash", models.CharField(blank=True, max_length=64)),
                ("chain_tx_id", models.CharField(blank=True, max_length=128)),
                ("reason", models.CharField(max_length=64)),
                ("status", models.CharField(choices=[("open", "Open"), ("acknowledged", "Acknowledged"), ("resolved", "Resolved")], db_index=True, default="open", max_length=16)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "audit_log",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="integrity_alerts",
                        to="audit.auditlog",
                    ),
                ),
                (
                    "integrity_check",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="alerts",
                        to="audit.integritycheck",
                    ),
                ),
            ],
            options={
                "db_table": "audit_integrity_alert",
                "ordering": ["-created_at"],
            },
        ),
    ]
