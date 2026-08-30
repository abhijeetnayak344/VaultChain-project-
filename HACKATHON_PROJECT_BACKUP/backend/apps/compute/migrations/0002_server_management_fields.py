# Extend Server with management fields and unique identifiers.

from django.db import migrations, models


def backfill_server_fields(apps, schema_editor):
    Server = apps.get_model("compute", "Server")
    for index, server in enumerate(Server.objects.all().order_by("hostname"), start=1):
        hostname = server.hostname or f"host-{index}"
        if not server.code:
            server.code = f"SRV-{index:04d}"
        if not server.name:
            server.name = hostname
        if not server.ip_address:
            server.ip_address = f"10.20.0.{index}"
        if not server.operating_system:
            server.operating_system = "Ubuntu 22.04 LTS"
        if not server.location:
            server.location = "AICTE HQ DC"
        server.save()


class Migration(migrations.Migration):
    dependencies = [
        ("compute", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="server",
            name="code",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AddField(
            model_name="server",
            name="name",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="server",
            name="ip_address",
            field=models.GenericIPAddressField(blank=True, null=True, protocol="both", unpack_ipv4=True),
        ),
        migrations.AddField(
            model_name="server",
            name="operating_system",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="server",
            name="location",
            field=models.CharField(blank=True, db_index=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="server",
            name="storage_percent",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.RunPython(backfill_server_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="server",
            name="code",
            field=models.CharField(max_length=32, unique=True, verbose_name="server ID"),
        ),
        migrations.AlterField(
            model_name="server",
            name="name",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="server",
            name="ip_address",
            field=models.GenericIPAddressField(protocol="both", unique=True, unpack_ipv4=True),
        ),
        migrations.AlterField(
            model_name="server",
            name="operating_system",
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name="server",
            name="location",
            field=models.CharField(db_index=True, max_length=128),
        ),
        migrations.AlterModelOptions(
            name="server",
            options={"ordering": ["name"]},
        ),
        migrations.AddIndex(
            model_name="server",
            index=models.Index(fields=["status", "location"], name="compute_ser_status_loc_idx"),
        ),
    ]
