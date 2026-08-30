import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """Append-only security audit event. Rows are never updated or deleted via the API."""

    class Action(models.TextChoices):
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        SERVER_CREATE = "server.create", "Server created"
        SERVER_UPDATE = "server.update", "Server updated"
        SERVER_DELETE = "server.delete", "Server deleted"
        FIREWALL_CREATE = "firewall.create", "Firewall created"
        FIREWALL_UPDATE = "firewall.update", "Firewall updated"
        FIREWALL_REQUEST = "firewall.request", "Firewall change requested"
        APPROVAL_APPROVE = "approval.approve", "Change approved"
        APPROVAL_REJECT = "approval.reject", "Change rejected"
        USER_CREATE = "user.create", "User created"
        USER_UPDATE = "user.update", "User updated"
        USER_DISABLE = "user.disable", "User disabled"
        USER_PASSWORD = "user.password_change", "Password changed"
        ROLE_CREATE = "role.create", "Role created"
        ROLE_UPDATE = "role.update", "Role updated"
        ROLE_ASSIGN = "role.assign", "Roles assigned"

    class ResourceType(models.TextChoices):
        USER = "user", "User"
        ROLE = "role", "Role"
        SERVER = "server", "Server"
        FIREWALL = "firewall", "Firewall"
        APPROVAL = "approval", "Approval"
        SESSION = "session", "Session"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    actor_email = models.EmailField(blank=True)
    action = models.CharField(max_length=64, db_index=True)
    resource_type = models.CharField(max_length=32, db_index=True)
    resource_id = models.CharField(max_length=64, blank=True, db_index=True)
    ip_address = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    integrity_hash = models.CharField(max_length=64, blank=True, db_index=True)
    chain_tx_id = models.CharField(max_length=128, blank=True)
    chain_status = models.CharField(max_length=16, default="skipped", db_index=True)
    verification_status = models.CharField(max_length=16, default="unverified", db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True, editable=False)

    class Meta:
        db_table = "audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "created_at"], name="audit_action_time_idx"),
            models.Index(fields=["resource_type", "created_at"], name="audit_resource_time_idx"),
        ]

    def __str__(self):
        return f"{self.action} {self.resource_type}:{self.resource_id}"


class IntegrityCheck(models.Model):
    """One verification run: current data hash vs blockchain hash."""

    class Result(models.TextChoices):
        VERIFIED = "verified", "Verified"
        ALERT = "alert", "Security alert"
        NOT_ANCHORED = "not_anchored", "Not anchored"
        UNAVAILABLE = "unavailable", "Fabric unavailable"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit_log = models.ForeignKey(AuditLog, on_delete=models.CASCADE, related_name="integrity_checks")
    current_hash = models.CharField(max_length=64)
    blockchain_hash = models.CharField(max_length=64, blank=True)
    stored_hash = models.CharField(max_length=64, blank=True)
    chain_tx_id = models.CharField(max_length=128, blank=True)
    result = models.CharField(max_length=16, choices=Result.choices, db_index=True)
    reason = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "audit_integrity_check"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.result} {self.audit_log_id}"


class IntegrityAlert(models.Model):
    """Open security alert when current data hash does not match the blockchain hash."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit_log = models.ForeignKey(AuditLog, on_delete=models.CASCADE, related_name="integrity_alerts")
    integrity_check = models.ForeignKey(
        IntegrityCheck,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
    )
    local_hash = models.CharField(max_length=64)
    chain_hash = models.CharField(max_length=64, blank=True)
    chain_tx_id = models.CharField(max_length=128, blank=True)
    reason = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "audit_integrity_alert"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.status} {self.audit_log_id}"
