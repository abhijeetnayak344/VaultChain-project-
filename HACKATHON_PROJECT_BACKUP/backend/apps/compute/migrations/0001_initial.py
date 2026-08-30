# Generated for dashboard server inventory.

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Server",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("hostname", models.CharField(max_length=128, unique=True)),
                ("environment", models.CharField(default="production", max_length=32)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("online", "Online"),
                            ("offline", "Offline"),
                            ("maintenance", "Maintenance"),
                        ],
                        db_index=True,
                        default="online",
                        max_length=16,
                    ),
                ),
                ("cpu_percent", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("ram_percent", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "compute_server",
                "ordering": ["hostname"],
            },
        ),
    ]
