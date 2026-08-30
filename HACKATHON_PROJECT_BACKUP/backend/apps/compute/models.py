import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Server(models.Model):
    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        MAINTENANCE = "maintenance", "Maintenance"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField("server ID", max_length=32, unique=True, blank=True)
    name = models.CharField(max_length=128)
    hostname = models.CharField(max_length=128, unique=True)
    ip_address = models.GenericIPAddressField(protocol="both", unpack_ipv4=True, unique=True)
    operating_system = models.CharField(max_length=64)
    location = models.CharField(max_length=128, db_index=True)
    environment = models.CharField(max_length=32, default="production")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ONLINE, db_index=True)
    cpu_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    ram_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    storage_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "compute_server"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status", "location"], name="compute_ser_status_loc_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"SRV-{uuid.uuid4().hex[:8].upper()}"
        self.hostname = (self.hostname or "").strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} {self.hostname}"
