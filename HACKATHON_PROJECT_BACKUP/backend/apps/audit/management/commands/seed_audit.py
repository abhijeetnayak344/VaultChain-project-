from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.compute.models import Server
from apps.network.models import Firewall, FirewallChangeRequest


class Command(BaseCommand):
    help = "Seed sample security audit logs for the audit dashboard."

    def handle(self, *args, **options):
        if AuditLog.objects.exists():
            self.stdout.write("Audit logs already present; skipping seed.")
            return

        actor = User.objects.filter(is_active=True).order_by("date_joined").first()
        email = actor.email if actor else "dcim-admin@aicte.gov.in"
        server = Server.objects.order_by("name").first()
        firewall = Firewall.objects.order_by("name").first()
        request = FirewallChangeRequest.objects.order_by("-requested_at").first()
        now = timezone.now()

        samples = [
            (AuditLog.Action.LOGIN, AuditLog.ResourceType.SESSION, str(actor.pk) if actor else "", 2, "10.20.1.40"),
            (AuditLog.Action.LOGOUT, AuditLog.ResourceType.SESSION, str(actor.pk) if actor else "", 26, "10.20.1.40"),
            (
                AuditLog.Action.SERVER_CREATE,
                AuditLog.ResourceType.SERVER,
                str(server.pk) if server else "",
                20,
                "10.20.1.40",
            ),
            (
                AuditLog.Action.SERVER_UPDATE,
                AuditLog.ResourceType.SERVER,
                str(server.pk) if server else "",
                8,
                "10.20.1.40",
            ),
            (
                AuditLog.Action.FIREWALL_CREATE,
                AuditLog.ResourceType.FIREWALL,
                str(firewall.pk) if firewall else "",
                18,
                "10.20.8.12",
            ),
            (
                AuditLog.Action.FIREWALL_REQUEST,
                AuditLog.ResourceType.FIREWALL,
                str(request.pk) if request else "",
                6,
                "10.20.8.12",
            ),
            (
                AuditLog.Action.APPROVAL_APPROVE,
                AuditLog.ResourceType.APPROVAL,
                str(request.pk) if request else "",
                4,
                "10.20.1.50",
            ),
            (AuditLog.Action.USER_UPDATE, AuditLog.ResourceType.USER, str(actor.pk) if actor else "", 12, "10.20.1.40"),
            (AuditLog.Action.ROLE_ASSIGN, AuditLog.ResourceType.USER, str(actor.pk) if actor else "", 10, "10.20.1.40"),
            (AuditLog.Action.LOGIN, AuditLog.ResourceType.SESSION, str(actor.pk) if actor else "", 1, "10.20.1.40"),
        ]

        for action, resource_type, resource_id, hours_ago, ip in samples:
            AuditLog.objects.create(
                actor=actor,
                actor_email=email,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip,
                details={"outcome": "success", "seeded": True},
                created_at=now - timedelta(hours=hours_ago),
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(samples)} audit log entries."))
