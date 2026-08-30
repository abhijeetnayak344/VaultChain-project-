"""Firewall rule change approval engine."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.network.models import FirewallApprovalEvent, FirewallChangeRequest, FirewallRule


def pending_approval_count():
    return FirewallChangeRequest.objects.filter(status=FirewallChangeRequest.Status.PENDING).count()


def rule_payload(rule):
    if rule is None:
        return {}
    return {
        "source_ip": rule.source_ip,
        "destination_ip": rule.destination_ip,
        "port": rule.port,
        "protocol": rule.protocol,
        "action": rule.action,
    }


def _record_event(change_request, event_type, actor, comment=""):
    return FirewallApprovalEvent.objects.create(
        change_request=change_request,
        event_type=event_type,
        actor=actor,
        comment=comment or "",
    )


@transaction.atomic
def submit_change(*, user, firewall, change_type, rule=None, fields=None, comment=""):
    fields = fields or {}
    if change_type in (FirewallChangeRequest.ChangeType.UPDATE, FirewallChangeRequest.ChangeType.DELETE):
        if rule is None:
            raise ValidationError("An existing rule is required to edit or delete.")
        if rule.firewall_id != firewall.id:
            raise ValidationError("Rule does not belong to this firewall.")
        pending = FirewallChangeRequest.objects.filter(
            rule=rule,
            status=FirewallChangeRequest.Status.PENDING,
        ).exists()
        if pending:
            raise ValidationError("This rule already has a pending change request.")

    if change_type == FirewallChangeRequest.ChangeType.DELETE:
        fields = rule_payload(rule)
    elif change_type == FirewallChangeRequest.ChangeType.UPDATE:
        merged = rule_payload(rule)
        merged.update(fields)
        fields = merged

    change_request = FirewallChangeRequest.objects.create(
        firewall=firewall,
        rule=rule,
        change_type=change_type,
        source_ip=fields.get("source_ip") or "",
        destination_ip=fields.get("destination_ip") or "",
        port=fields.get("port"),
        protocol=fields.get("protocol") or "",
        action=fields.get("action") or "",
        request_comment=comment or "",
        requested_by=user,
        status=FirewallChangeRequest.Status.PENDING,
    )
    _record_event(change_request, FirewallApprovalEvent.EventType.REQUESTED, user, comment)
    return change_request


def _apply_approved_change(change_request):
    fields = {
        "source_ip": change_request.source_ip,
        "destination_ip": change_request.destination_ip,
        "port": change_request.port,
        "protocol": change_request.protocol,
        "action": change_request.action,
    }
    if change_request.change_type == FirewallChangeRequest.ChangeType.CREATE:
        FirewallRule.objects.create(firewall=change_request.firewall, **fields)
        return
    if change_request.rule is None:
        raise ValidationError("The target rule no longer exists.")
    if change_request.change_type == FirewallChangeRequest.ChangeType.UPDATE:
        for key, value in fields.items():
            setattr(change_request.rule, key, value)
        change_request.rule.save()
        return
    if change_request.change_type == FirewallChangeRequest.ChangeType.DELETE:
        change_request.rule.delete()
        change_request.rule = None


@transaction.atomic
def decide_change(*, user, change_request, approved, comment=""):
    if change_request.status != FirewallChangeRequest.Status.PENDING:
        raise ValidationError("Only pending requests can be reviewed.")
    if change_request.requested_by_id and change_request.requested_by_id == user.id:
        raise PermissionDenied("You cannot approve or reject your own firewall change.")

    if approved:
        _apply_approved_change(change_request)
        change_request.status = FirewallChangeRequest.Status.APPROVED
        event_type = FirewallApprovalEvent.EventType.APPROVED
    else:
        if not (comment or "").strip():
            raise ValidationError("A rejection reason is required.")
        change_request.status = FirewallChangeRequest.Status.REJECTED
        event_type = FirewallApprovalEvent.EventType.REJECTED

    change_request.review_comment = comment or ""
    change_request.reviewed_by = user
    change_request.reviewed_at = timezone.now()
    change_request.save(update_fields=["status", "review_comment", "reviewed_by", "reviewed_at", "rule"])
    _record_event(change_request, event_type, user, comment)
    return change_request
