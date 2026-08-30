"""Write path for security audit events. Other apps should call record_event, not the model."""

from apps.audit.models import AuditLog


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR") or ""
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.META.get("REMOTE_ADDR") or "")[:64]


def record_event(
    *,
    action,
    resource_type,
    actor=None,
    actor_email="",
    resource_id="",
    ip_address="",
    details=None,
):
    email = actor_email
    if not email and actor is not None:
        email = getattr(actor, "email", "") or ""
    log = AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        actor_email=email,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id or "")[:64],
        ip_address=ip_address or "",
        details=details or {},
    )
    from apps.audit.blockchain import schedule_anchor

    schedule_anchor(log)
    return log


def summary(hours=24):
    from datetime import timedelta

    from django.db.models import Count
    from django.utils import timezone

    since = timezone.now() - timedelta(hours=hours)
    recent = AuditLog.objects.filter(created_at__gte=since)
    return {
        "total": AuditLog.objects.count(),
        "last_24h": recent.count(),
        "logins_24h": recent.filter(action=AuditLog.Action.LOGIN).count(),
        "approvals_24h": recent.filter(
            action__in=(AuditLog.Action.APPROVAL_APPROVE, AuditLog.Action.APPROVAL_REJECT)
        ).count(),
        "by_resource_type": list(
            AuditLog.objects.values("resource_type").annotate(count=Count("id")).order_by("-count")
        ),
        "by_action": list(recent.values("action").annotate(count=Count("id")).order_by("-count")[:12]),
    }
