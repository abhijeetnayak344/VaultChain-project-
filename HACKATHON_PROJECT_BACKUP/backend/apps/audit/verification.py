"""Compare current audit data hashes with Hyperledger Fabric hashes."""

from __future__ import annotations

import logging

from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from apps.audit.blockchain import CRITICAL_RESOURCE_TYPES, event_hash, fetch_chain_integrity
from apps.audit.models import AuditLog, IntegrityAlert, IntegrityCheck

logger = logging.getLogger(__name__)

STATUS_VERIFIED = "verified"
STATUS_ALERT = "alert"
STATUS_NOT_ANCHORED = "not_anchored"
STATUS_UNAVAILABLE = "unavailable"
STATUS_UNVERIFIED = "unverified"

STATUS_LABELS = {
    STATUS_VERIFIED: "VERIFIED",
    STATUS_ALERT: "SECURITY ALERT",
    STATUS_NOT_ANCHORED: "NOT ANCHORED",
    STATUS_UNAVAILABLE: "UNAVAILABLE",
    STATUS_UNVERIFIED: "UNVERIFIED",
}


def classify_integrity(
    *,
    current_hash,
    stored_hash="",
    chain_hash="",
    anchored=False,
    fabric_enabled=True,
    fabric_reachable=True,
):
    """Current data hash vs blockchain hash. Match → VERIFIED; mismatch → SECURITY ALERT."""
    if stored_hash and current_hash != stored_hash:
        return {"status": STATUS_ALERT, "reason": "local_hash_mismatch", "matches": False}
    if not fabric_enabled:
        return {"status": STATUS_NOT_ANCHORED, "reason": "fabric_disabled", "matches": False}
    if not fabric_reachable:
        return {"status": STATUS_UNAVAILABLE, "reason": "fabric_unavailable", "matches": False}
    if not anchored or not chain_hash:
        return {"status": STATUS_NOT_ANCHORED, "reason": "not_anchored", "matches": False}
    if current_hash == chain_hash:
        return {"status": STATUS_VERIFIED, "reason": "match", "matches": True}
    return {"status": STATUS_ALERT, "reason": "blockchain_hash_mismatch", "matches": False}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, (status or "").upper() or "UNVERIFIED")


def _persist_status(log: AuditLog, status: str) -> str:
    stored = status if status in {STATUS_VERIFIED, STATUS_ALERT} else STATUS_UNVERIFIED
    AuditLog.objects.filter(pk=log.pk).update(verification_status=stored)
    return stored


def _open_alert(log: AuditLog, check: IntegrityCheck, current_hash: str, chain_hash: str, tx_id: str, reason: str) -> None:
    existing = IntegrityAlert.objects.filter(audit_log=log, status=IntegrityAlert.Status.OPEN).first()
    if existing:
        existing.integrity_check = check
        existing.local_hash = current_hash
        existing.chain_hash = chain_hash
        existing.chain_tx_id = tx_id
        existing.reason = reason
        existing.save(update_fields=["integrity_check", "local_hash", "chain_hash", "chain_tx_id", "reason", "updated_at"])
        return
    IntegrityAlert.objects.create(
        audit_log=log,
        integrity_check=check,
        local_hash=current_hash,
        chain_hash=chain_hash,
        chain_tx_id=tx_id,
        reason=reason,
        status=IntegrityAlert.Status.OPEN,
    )
    try:
        from apps.monitoring.services import raise_alert

        raise_alert(
            title=f"Blockchain integrity mismatch: {log.action} {log.resource_id or log.id}",
            source="blockchain",
            severity="critical",
        )
    except Exception:
        logger.exception("Failed to raise monitoring alert for audit %s", log.pk)


def _resolve_open_alerts(log: AuditLog) -> None:
    IntegrityAlert.objects.filter(audit_log=log, status=IntegrityAlert.Status.OPEN).update(
        status=IntegrityAlert.Status.RESOLVED,
        updated_at=timezone.now(),
    )


def record_anchor_success(log: AuditLog, digest: str, tx_id: str) -> None:
    IntegrityCheck.objects.create(
        audit_log=log,
        current_hash=digest,
        blockchain_hash=digest,
        stored_hash=digest,
        chain_tx_id=tx_id,
        result=STATUS_VERIFIED,
        reason="anchored",
        details={"source": "anchor"},
    )
    _persist_status(log, STATUS_VERIFIED)
    _resolve_open_alerts(log)


def verify_and_record(log: AuditLog) -> dict:
    log = AuditLog.objects.filter(pk=log.pk).first() or log
    current = event_hash(log)
    stored = log.integrity_hash or ""
    chain = fetch_chain_integrity(str(log.id), current)
    chain_hash = chain.get("onChainHash") or ""
    tx_id = chain.get("txId") or log.chain_tx_id or ""
    classified = classify_integrity(
        current_hash=current,
        stored_hash=stored,
        chain_hash=chain_hash,
        anchored=bool(chain.get("anchored")),
        fabric_enabled=bool(chain.get("fabric_enabled")),
        fabric_reachable=bool(chain.get("fabric_reachable")),
    )
    check = IntegrityCheck.objects.create(
        audit_log=log,
        current_hash=current,
        blockchain_hash=chain_hash,
        stored_hash=stored,
        chain_tx_id=tx_id,
        result=classified["status"],
        reason=classified["reason"],
        details={"fabric": chain.get("raw") or {}},
    )
    stored_status = _persist_status(log, classified["status"])
    if classified["status"] == STATUS_ALERT:
        _open_alert(log, check, current, chain_hash, tx_id, classified["reason"])
    elif classified["status"] == STATUS_VERIFIED:
        _resolve_open_alerts(log)

    return {
        "log_id": str(log.id),
        "check_id": str(check.id),
        "status": classified["status"],
        "verification_status": stored_status,
        "label": status_label(classified["status"]),
        "matches": classified["matches"],
        "reason": classified["reason"],
        "current_hash": current,
        "blockchain_hash": chain_hash,
        "stored_hash": stored,
        "chain_tx_id": tx_id,
        "chain_status": log.chain_status,
        "fabric_enabled": bool(chain.get("fabric_enabled")),
    }


def verify_recent(*, limit: int = 25, log_ids=None) -> list[dict]:
    queryset = AuditLog.objects.filter(resource_type__in=CRITICAL_RESOURCE_TYPES).order_by("-created_at")
    if log_ids:
        queryset = queryset.filter(pk__in=log_ids)
    else:
        queryset = queryset[: max(1, min(int(limit), 100))]
    return [verify_and_record(log) for log in queryset]


def blockchain_summary() -> dict:
    logs = AuditLog.objects.all()
    last_check = IntegrityCheck.objects.order_by("-created_at").values_list("created_at", flat=True).first()
    by_result = list(
        IntegrityCheck.objects.values("result").annotate(count=Count("id")).order_by("-count")
    )
    return {
        "critical_events": logs.filter(resource_type__in=CRITICAL_RESOURCE_TYPES).count(),
        "hashed": logs.exclude(integrity_hash="").count(),
        "anchored": logs.filter(chain_status="anchored").count(),
        "pending": logs.filter(chain_status="pending").count(),
        "failed": logs.filter(chain_status="failed").count(),
        "verified": logs.filter(verification_status=STATUS_VERIFIED).count(),
        "alerts_open": IntegrityAlert.objects.filter(status=IntegrityAlert.Status.OPEN).count(),
        "alerts_acknowledged": IntegrityAlert.objects.filter(status=IntegrityAlert.Status.ACKNOWLEDGED).count(),
        "alerts_total": IntegrityAlert.objects.count(),
        "checks": IntegrityCheck.objects.count(),
        "by_check_result": by_result,
        "fabric_enabled": bool(getattr(settings, "FABRIC_ENABLED", False)),
        "last_check_at": last_check.isoformat() if last_check else None,
    }


def set_alert_status(alert: IntegrityAlert, status: str) -> IntegrityAlert:
    alert.status = status
    alert.save(update_fields=["status", "updated_at"])
    return alert
