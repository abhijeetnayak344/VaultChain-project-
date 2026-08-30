# Store SHA-256 hashes of audit rows on Hyperledger Fabric. Never send raw PII to the peer.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="integrity_hash",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="chain_tx_id",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="chain_status",
            field=models.CharField(db_index=True, default="skipped", max_length=16),
        ),
    ]
