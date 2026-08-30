"""Hash audit rows and submit them to the Fabric Gateway anchor. Keys never leave the Fabric stack."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction

from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)

CRITICAL_RESOURCE_TYPES = {
    AuditLog.ResourceType.SERVER,
    AuditLog.ResourceType.FIREWALL,
    AuditLog.ResourceType.APPROVAL,
    AuditLog.ResourceType.USER,
    AuditLog.ResourceType.ROLE,
    AuditLog.ResourceType.SESSION,
}


def event_hash(log: AuditLog) -> str:
    payload = {
        "log_id": str(log.id),
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "actor_email": log.actor_email,
        "timestamp": log.created_at.isoformat(),
        "ip_address": log.ip_address,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _anchor_url(path: str) -> str:
    base = (getattr(settings, "FABRIC_ANCHOR_URL", "") or "").rstrip("/")
    return f"{base}{path}"


def _post(path: str, body: dict, timeout: int = 12) -> dict:
    request = Request(
        _anchor_url(path),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def _get(path: str, timeout: int = 12) -> dict:
    request = Request(_anchor_url(path), method="GET")
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def chaincode_call(log: AuditLog, digest: str) -> tuple[str, list[str]]:
    timestamp = log.created_at.isoformat()
    event_id = str(log.id)
    if log.resource_type == AuditLog.ResourceType.SERVER:
        return "recordServerChange", [event_id, digest, log.resource_id or event_id, timestamp]
    if log.resource_type in {AuditLog.ResourceType.FIREWALL, AuditLog.ResourceType.APPROVAL}:
        return "recordFirewallChange", [event_id, digest, log.resource_id or event_id, timestamp]
    return "recordAuditEvent", [event_id, digest, log.resource_type, timestamp]


def fetch_chain_integrity(event_id: str, digest: str) -> dict:
    if not getattr(settings, "FABRIC_ENABLED", False):
        return {
            "fabric_enabled": False,
            "fabric_reachable": False,
            "anchored": False,
            "onChainHash": "",
            "txId": "",
            "raw": {"reason": "fabric_disabled"},
        }
    try:
        remote = _post("/api/v1/verify", {"eventId": str(event_id), "hash": digest})
        return {
            "fabric_enabled": True,
            "fabric_reachable": True,
            "anchored": bool(remote.get("anchored")),
            "onChainHash": remote.get("onChainHash") or "",
            "txId": remote.get("txId") or "",
            "raw": remote,
        }
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning("Fabric verify failed for %s: %s", event_id, exc)
        return {
            "fabric_enabled": True,
            "fabric_reachable": False,
            "anchored": False,
            "onChainHash": "",
            "txId": "",
            "raw": {"reason": str(exc)},
        }


def anchor_log(log_id: str) -> None:
    log = AuditLog.objects.filter(pk=log_id).first()
    if log is None:
        return
    digest = event_hash(log)
    function, args = chaincode_call(log, digest)
    try:
        result = _post("/api/v1/anchor", {"function": function, "args": args})
        tx_id = ""
        if isinstance(result.get("result"), dict):
            tx_id = result["result"].get("txId") or ""
        AuditLog.objects.filter(pk=log.pk).update(
            integrity_hash=digest,
            chain_tx_id=tx_id,
            chain_status="anchored",
        )
        log.refresh_from_db()
        from apps.audit.verification import record_anchor_success

        record_anchor_success(log, digest, tx_id)
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning("Fabric anchor failed for %s: %s", log_id, exc)
        AuditLog.objects.filter(pk=log.pk).update(integrity_hash=digest, chain_status="failed")


def schedule_anchor(log: AuditLog) -> None:
    if log.resource_type not in CRITICAL_RESOURCE_TYPES:
        return
    digest = event_hash(log)
    if not getattr(settings, "FABRIC_ENABLED", False):
        AuditLog.objects.filter(pk=log.pk).update(
            integrity_hash=digest,
            chain_status="skipped",
            verification_status="unverified",
        )
        return
    AuditLog.objects.filter(pk=log.pk).update(
        integrity_hash=digest,
        chain_status="pending",
        verification_status="unverified",
    )
    log_id = str(log.pk)
    transaction.on_commit(lambda: threading.Thread(target=anchor_log, args=(log_id,), daemon=True).start())


def verify_log(log: AuditLog) -> dict:
    from apps.audit.verification import verify_and_record

    return verify_and_record(log)


def chain_history(event_id: str) -> dict:
    if not getattr(settings, "FABRIC_ENABLED", False):
        return {"reason": "fabric_disabled"}
    try:
        return _get(f"/api/v1/history/{event_id}")
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {"reason": str(exc)}
