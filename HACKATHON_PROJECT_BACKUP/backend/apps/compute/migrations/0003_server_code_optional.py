# Allow blank server ID so the model can auto-assign SRV-XXXXXXXX.

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("compute", "0002_server_management_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="server",
            name="code",
            field=models.CharField(
                blank=True,
                max_length=32,
                unique=True,
                verbose_name="server ID",
            ),
        ),
        migrations.AlterField(
            model_name="server",
            name="cpu_percent",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=5,
                validators=[MinValueValidator(0), MaxValueValidator(100)],
            ),
        ),
        migrations.AlterField(
            model_name="server",
            name="ram_percent",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=5,
                validators=[MinValueValidator(0), MaxValueValidator(100)],
            ),
        ),
        migrations.AlterField(
            model_name="server",
            name="storage_percent",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=5,
                validators=[MinValueValidator(0), MaxValueValidator(100)],
            ),
        ),
    ]
