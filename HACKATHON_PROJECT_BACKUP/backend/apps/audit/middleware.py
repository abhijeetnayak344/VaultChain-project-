"""Map mutating API routes to audit actions. Keep this table as the single catalog."""

import json
import logging
import re

from apps.audit.models import AuditLog
from apps.audit.services import client_ip, record_event

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {
    "password",
    "new_password",
    "old_password",
    "current_password",
    "refresh",
    "access",
    "token",
}

# More specific paths first.
AUDIT_RULES = (
    (re.compile(r"^/api/v1/auth/login/?$"), {"POST"}, AuditLog.Action.LOGIN, AuditLog.ResourceType.SESSION, None, True),
    (re.compile(r"^/api/v1/auth/logout/?$"), {"POST"}, AuditLog.Action.LOGOUT, AuditLog.ResourceType.SESSION, None, False),
    (
        re.compile(r"^/api/v1/auth/change-password/?$"),
        {"POST"},
        AuditLog.Action.USER_PASSWORD,
        AuditLog.ResourceType.USER,
        None,
        False,
    ),
    (re.compile(r"^/api/v1/auth/me/?$"), {"PATCH", "PUT"}, AuditLog.Action.USER_UPDATE, AuditLog.ResourceType.USER, None, False),
    (
        re.compile(r"^/api/v1/users/([^/]+)/disable/?$"),
        {"POST"},
        AuditLog.Action.USER_DISABLE,
        AuditLog.ResourceType.USER,
        1,
        False,
    ),
    (
        re.compile(r"^/api/v1/users/([^/]+)/roles/?$"),
        {"POST"},
        AuditLog.Action.ROLE_ASSIGN,
        AuditLog.ResourceType.USER,
        1,
        False,
    ),
    (re.compile(r"^/api/v1/users/?$"), {"POST"}, AuditLog.Action.USER_CREATE, AuditLog.ResourceType.USER, None, False),
    (
        re.compile(r"^/api/v1/users/([^/]+)/?$"),
        {"PATCH", "PUT"},
        AuditLog.Action.USER_UPDATE,
        AuditLog.ResourceType.USER,
        1,
        False,
    ),
    (re.compile(r"^/api/v1/roles/?$"), {"POST"}, AuditLog.Action.ROLE_CREATE, AuditLog.ResourceType.ROLE, None, False),
    (
        re.compile(r"^/api/v1/roles/([^/]+)/?$"),
        {"PATCH", "PUT"},
        AuditLog.Action.ROLE_UPDATE,
        AuditLog.ResourceType.ROLE,
        1,
        False,
    ),
    (re.compile(r"^/api/v1/servers/?$"), {"POST"}, AuditLog.Action.SERVER_CREATE, AuditLog.ResourceType.SERVER, None, False),
    (
        re.compile(r"^/api/v1/servers/([^/]+)/?$"),
        {"PATCH", "PUT"},
        AuditLog.Action.SERVER_UPDATE,
        AuditLog.ResourceType.SERVER,
        1,
        False,
    ),
    (
        re.compile(r"^/api/v1/servers/([^/]+)/?$"),
        {"DELETE"},
        AuditLog.Action.SERVER_DELETE,
        AuditLog.ResourceType.SERVER,
        1,
        False,
    ),
    (
        re.compile(r"^/api/v1/firewalls/?$"),
        {"POST"},
        AuditLog.Action.FIREWALL_CREATE,
        AuditLog.ResourceType.FIREWALL,
        None,
        False,
    ),
    (
        re.compile(r"^/api/v1/firewalls/([^/]+)/?$"),
        {"PATCH", "PUT"},
        AuditLog.Action.FIREWALL_UPDATE,
        AuditLog.ResourceType.FIREWALL,
        1,
        False,
    ),
    (
        re.compile(r"^/api/v1/firewall-change-requests/([^/]+)/approve/?$"),
        {"POST"},
        AuditLog.Action.APPROVAL_APPROVE,
        AuditLog.ResourceType.APPROVAL,
        1,
        False,
    ),
    (
        re.compile(r"^/api/v1/firewall-change-requests/([^/]+)/reject/?$"),
        {"POST"},
        AuditLog.Action.APPROVAL_REJECT,
        AuditLog.ResourceType.APPROVAL,
        1,
        False,
    ),
    (
        re.compile(r"^/api/v1/firewall-change-requests/?$"),
        {"POST"},
        AuditLog.Action.FIREWALL_REQUEST,
        AuditLog.ResourceType.FIREWALL,
        None,
        False,
    ),
)


def _json_body(raw):
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _scrub(payload):
    if not isinstance(payload, dict):
        return {}
    clean = {}
    for key, value in payload.items():
        if str(key).lower() in SENSITIVE_KEYS:
            clean[key] = "[redacted]"
        else:
            clean[key] = value
    return clean


def _resource_id_from_response(body, resource_type, action=""):
    if not isinstance(body, dict):
        return ""
    if action == AuditLog.Action.FIREWALL_REQUEST:
        return str(body.get("request_id") or body.get("firewall_id") or body.get("id") or "")
    if resource_type == AuditLog.ResourceType.SERVER:
        return str(body.get("server_id") or body.get("id") or "")
    if resource_type == AuditLog.ResourceType.FIREWALL:
        return str(body.get("firewall_id") or body.get("request_id") or body.get("id") or "")
    if resource_type == AuditLog.ResourceType.APPROVAL:
        return str(body.get("request_id") or body.get("id") or "")
    if resource_type == AuditLog.ResourceType.USER:
        nested = body.get("user") if isinstance(body.get("user"), dict) else body
        return str(nested.get("id") or "")
    if resource_type == AuditLog.ResourceType.ROLE:
        return str(body.get("id") or "")
    if resource_type == AuditLog.ResourceType.SESSION:
        nested = body.get("user") if isinstance(body.get("user"), dict) else {}
        return str(nested.get("id") or "")
    return str(body.get("id") or "")


def match_rule(path, method):
    for pattern, methods, action, resource_type, group, log_failures in AUDIT_RULES:
        if method not in methods:
            continue
        matched = pattern.match(path)
        if matched:
            resource_id = matched.group(group) if group else ""
            return action, resource_type, resource_id, log_failures
    return None


class AuditLoggingMiddleware:
    """Records security-relevant API mutations after the view returns."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self._record(request, response)
        except Exception:
            logger.exception("Failed to write audit log")
        return response

    def _record(self, request, response):
        path = request.path
        if path.startswith("/api/v1/audit"):
            return
        method = request.method.upper()
        matched = match_rule(path, method)
        if not matched:
            return
        action, resource_type, resource_id, log_failures = matched
        status_code = getattr(response, "status_code", 500)
        if status_code >= 400 and not log_failures:
            return
        if status_code >= 500:
            return

        response_body = _json_body(getattr(response, "content", b"") or b"")
        request_body = _scrub(_json_body(getattr(request, "body", b"") or b""))
        if not resource_id:
            resource_id = _resource_id_from_response(response_body, resource_type, action)

        actor = getattr(request, "user", None)
        actor_email = ""
        if getattr(actor, "is_authenticated", False):
            actor_email = actor.email
            if not resource_id:
                resource_id = str(actor.pk)
        elif action == AuditLog.Action.LOGIN:
            nested = response_body.get("user") if isinstance(response_body.get("user"), dict) else {}
            actor_email = nested.get("email") or request_body.get("email") or ""
            if nested.get("id"):
                from apps.accounts.models import User

                actor = User.objects.filter(pk=nested["id"]).first() or actor

        details = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "outcome": "success" if status_code < 400 else "failure",
        }
        if request_body:
            details["request"] = request_body

        record_event(
            actor=actor,
            actor_email=actor_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=client_ip(request),
            details=details,
        )
