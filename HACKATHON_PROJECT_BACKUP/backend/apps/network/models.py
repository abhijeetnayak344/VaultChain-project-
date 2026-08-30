import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Firewall(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    class Approval(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    vendor = models.CharField(max_length=64, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    approval_status = models.CharField(
        max_length=16,
        choices=Approval.choices,
        default=Approval.APPROVED,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "network_firewall"
        ordering = ["name"]

    def __str__(self):
        return self.name


class FirewallRule(models.Model):
    class Protocol(models.TextChoices):
        TCP = "tcp", "TCP"
        UDP = "udp", "UDP"
        ICMP = "icmp", "ICMP"
        ANY = "any", "Any"

    class Action(models.TextChoices):
        ALLOW = "allow", "Allow"
        DENY = "deny", "Deny"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firewall = models.ForeignKey(Firewall, on_delete=models.CASCADE, related_name="rules")
    source_ip = models.CharField(max_length=64)
    destination_ip = models.CharField(max_length=64)
    port = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
    )
    protocol = models.CharField(max_length=8, choices=Protocol.choices)
    action = models.CharField(max_length=8, choices=Action.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "network_firewall_rule"
        ordering = ["firewall__name", "action", "protocol", "port"]
        indexes = [
            models.Index(fields=["firewall", "action"], name="net_fw_rule_fw_action_idx"),
        ]

    def __str__(self):
        port = self.port if self.port is not None else "*"
        return f"{self.action} {self.protocol}/{port} {self.source_ip}->{self.destination_ip}"


class FirewallChangeRequest(models.Model):
    class ChangeType(models.TextChoices):
        CREATE = "create", "Add rule"
        UPDATE = "update", "Edit rule"
        DELETE = "delete", "Delete rule"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firewall = models.ForeignKey(Firewall, on_delete=models.CASCADE, related_name="change_requests")
    rule = models.ForeignKey(
        FirewallRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="change_requests",
    )
    change_type = models.CharField(max_length=16, choices=ChangeType.choices)
    source_ip = models.CharField(max_length=64, blank=True)
    destination_ip = models.CharField(max_length=64, blank=True)
    port = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
    )
    protocol = models.CharField(max_length=8, blank=True)
    action = models.CharField(max_length=8, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    request_comment = models.CharField(max_length=255, blank=True)
    review_comment = models.CharField(max_length=255, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="firewall_change_requests",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="firewall_reviews",
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "network_firewall_change_request"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["status", "requested_at"], name="net_fw_req_status_time_idx"),
        ]

    def __str__(self):
        return f"{self.change_type} {self.firewall_id} ({self.status})"


class FirewallApprovalEvent(models.Model):
    class EventType(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    change_request = models.ForeignKey(
        FirewallChangeRequest,
        on_delete=models.CASCADE,
        related_name="history",
    )
    event_type = models.CharField(max_length=16, choices=EventType.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="firewall_approval_events",
    )
    comment = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "network_firewall_approval_event"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.event_type} {self.change_request_id}"
