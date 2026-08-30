from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("network", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="firewall",
            name="vendor",
            field=models.CharField(default="", max_length=64),
        ),
        migrations.AlterField(
            model_name="firewall",
            name="status",
            field=models.CharField(
                choices=[("active", "Active"), ("inactive", "Inactive")],
                db_index=True,
                default="active",
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="FirewallRule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("source_ip", models.CharField(max_length=64)),
                ("destination_ip", models.CharField(max_length=64)),
                (
                    "port",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(65535),
                        ],
                    ),
                ),
                (
                    "protocol",
                    models.CharField(
                        choices=[("tcp", "TCP"), ("udp", "UDP"), ("icmp", "ICMP"), ("any", "Any")],
                        max_length=8,
                    ),
                ),
                ("action", models.CharField(choices=[("allow", "Allow"), ("deny", "Deny")], max_length=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "firewall",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rules",
                        to="network.firewall",
                    ),
                ),
            ],
            options={
                "db_table": "network_firewall_rule",
                "ordering": ["firewall__name", "action", "protocol", "port"],
            },
        ),
        migrations.CreateModel(
            name="FirewallChangeRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "change_type",
                    models.CharField(
                        choices=[("create", "Add rule"), ("update", "Edit rule"), ("delete", "Delete rule")],
                        max_length=16,
                    ),
                ),
                ("source_ip", models.CharField(blank=True, max_length=64)),
                ("destination_ip", models.CharField(blank=True, max_length=64)),
                (
                    "port",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(65535),
                        ],
                    ),
                ),
                ("protocol", models.CharField(blank=True, max_length=8)),
                ("action", models.CharField(blank=True, max_length=8)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                        db_index=True,
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("request_comment", models.CharField(blank=True, max_length=255)),
                ("review_comment", models.CharField(blank=True, max_length=255)),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "firewall",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="change_requests",
                        to="network.firewall",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="firewall_change_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="firewall_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "rule",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="change_requests",
                        to="network.firewallrule",
                    ),
                ),
            ],
            options={
                "db_table": "network_firewall_change_request",
                "ordering": ["-requested_at"],
            },
        ),
        migrations.CreateModel(
            name="FirewallApprovalEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "event_type",
                    models.CharField(
                        choices=[("requested", "Requested"), ("approved", "Approved"), ("rejected", "Rejected")],
                        max_length=16,
                    ),
                ),
                ("comment", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="firewall_approval_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "change_request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="history",
                        to="network.firewallchangerequest",
                    ),
                ),
            ],
            options={
                "db_table": "network_firewall_approval_event",
                "ordering": ["created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="firewallrule",
            index=models.Index(fields=["firewall", "action"], name="net_fw_rule_fw_action_idx"),
        ),
        migrations.AddIndex(
            model_name="firewallchangerequest",
            index=models.Index(fields=["status", "requested_at"], name="net_fw_req_status_time_idx"),
        ),
    ]
