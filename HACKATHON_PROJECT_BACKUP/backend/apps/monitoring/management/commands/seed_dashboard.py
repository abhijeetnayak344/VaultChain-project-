from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.compute.models import Server
from apps.monitoring.models import Alert, ResourceMetric, SecurityEvent
from apps.network.models import Firewall, FirewallApprovalEvent, FirewallChangeRequest, FirewallRule


SERVERS = [
    ("SRV-0001", "HQ Web 01", "aicte-dc-web-01", "10.20.1.11", "Ubuntu 22.04 LTS", "online", "42.10", "61.40", "48.00", "AICTE HQ DC"),
    ("SRV-0002", "HQ Web 02", "aicte-dc-web-02", "10.20.1.12", "Ubuntu 22.04 LTS", "online", "38.70", "55.20", "44.10", "AICTE HQ DC"),
    ("SRV-0003", "HQ App 01", "aicte-dc-app-01", "10.20.2.11", "RHEL 9", "online", "67.30", "72.80", "58.40", "AICTE HQ DC"),
    ("SRV-0004", "HQ App 02", "aicte-dc-app-02", "10.20.2.12", "RHEL 9", "offline", "0.00", "0.00", "12.00", "AICTE HQ DC"),
    ("SRV-0005", "HQ DB 01", "aicte-dc-db-01", "10.20.3.11", "RHEL 9", "online", "51.90", "78.10", "71.20", "AICTE HQ DC"),
    ("SRV-0006", "HQ DB 02", "aicte-dc-db-02", "10.20.3.12", "RHEL 9", "online", "44.20", "69.50", "66.80", "AICTE HQ DC"),
    ("SRV-0007", "HQ VPN 01", "aicte-dc-vpn-01", "10.20.8.11", "Ubuntu 24.04 LTS", "online", "22.40", "31.00", "19.50", "AICTE HQ DC"),
    ("SRV-0008", "Noida Edge", "aicte-reg-noida-01", "10.30.1.11", "Ubuntu 22.04 LTS", "offline", "0.00", "0.00", "8.00", "Regional Noida"),
    ("SRV-0009", "Mumbai Edge", "aicte-reg-mumbai-01", "10.31.1.11", "Ubuntu 22.04 LTS", "online", "33.80", "48.60", "41.00", "Regional Mumbai"),
    ("SRV-0010", "Chennai Edge", "aicte-reg-chennai-01", "10.32.1.11", "Windows Server 2022", "maintenance", "12.00", "28.00", "36.00", "Regional Chennai"),
    ("SRV-0011", "HQ Backup 01", "aicte-dc-backup-01", "10.20.9.11", "Ubuntu 22.04 LTS", "online", "18.50", "41.20", "82.30", "AICTE HQ DC"),
    ("SRV-0012", "HQ SIEM 01", "aicte-dc-siem-01", "10.20.7.11", "Ubuntu 22.04 LTS", "online", "71.40", "64.90", "53.10", "AICTE HQ DC"),
]

FIREWALLS = [
    ("HQ-Edge-FW-01", "Palo Alto", "active"),
    ("HQ-Edge-FW-02", "Palo Alto", "active"),
    ("DC-Core-FW-01", "Fortinet", "active"),
    ("Regional-Noida-FW", "Cisco", "active"),
    ("Regional-Mumbai-FW", "Cisco", "inactive"),
    ("Regional-Chennai-FW", "Fortinet", "active"),
]

FIREWALL_RULES = [
    ("HQ-Edge-FW-01", "any", "10.20.1.0/24", 443, "tcp", "allow"),
    ("HQ-Edge-FW-01", "10.0.0.0/8", "10.20.8.11", 1194, "udp", "allow"),
    ("HQ-Edge-FW-01", "any", "10.20.1.11", 22, "tcp", "deny"),
    ("DC-Core-FW-01", "10.20.2.0/24", "10.20.3.11", 5432, "tcp", "allow"),
    ("DC-Core-FW-01", "any", "10.20.3.0/24", 3306, "tcp", "deny"),
    ("Regional-Mumbai-FW", "10.31.0.0/16", "10.20.1.0/24", 443, "tcp", "allow"),
]

PENDING_RULE_REQUESTS = [
    ("HQ-Edge-FW-02", "any", "10.20.2.11", 22, "tcp", "allow", "Allow jump-host SSH to HQ App 01"),
    ("Regional-Noida-FW", "10.30.1.0/24", "10.20.7.11", 443, "tcp", "allow", "Noida collectors to HQ SIEM"),
]

ALERT_TITLES = [
    ("critical", "open", "Multiple failed SSH logins on aicte-dc-app-01"),
    ("critical", "open", "Ransomware signature detected on backup VLAN"),
    ("critical", "acknowledged", "SIEM correlation: possible C2 beacon"),
    ("high", "open", "Firewall rule change awaiting Security Admin"),
    ("high", "open", "Disk latency above SLO on aicte-dc-db-01"),
    ("medium", "resolved", "Certificate expiring in 21 days"),
    ("medium", "open", "Unusual east-west traffic on app subnet"),
    ("low", "open", "NTP drift on regional node"),
]


class Command(BaseCommand):
    help = "Seed demo inventory, alerts, and metrics for the cybersecurity dashboard."

    def handle(self, *args, **options):
        now = timezone.now()
        servers = []
        for code, name, hostname, ip, os_name, status, cpu, ram, storage, location in SERVERS:
            server, _ = Server.objects.update_or_create(
                hostname=hostname,
                defaults={
                    "code": code,
                    "name": name,
                    "ip_address": ip,
                    "operating_system": os_name,
                    "status": status,
                    "cpu_percent": Decimal(cpu),
                    "ram_percent": Decimal(ram),
                    "storage_percent": Decimal(storage),
                    "location": location,
                    "environment": "production",
                    "last_seen_at": now if status == "online" else now - timedelta(hours=6),
                },
            )
            servers.append(server)

        firewalls = {}
        for name, vendor, status in FIREWALLS:
            firewall, _ = Firewall.objects.update_or_create(
                name=name,
                defaults={
                    "vendor": vendor,
                    "status": status,
                    "approval_status": Firewall.Approval.APPROVED,
                },
            )
            firewalls[name] = firewall

        for fw_name, source, dest, port, protocol, action in FIREWALL_RULES:
            FirewallRule.objects.get_or_create(
                firewall=firewalls[fw_name],
                source_ip=source,
                destination_ip=dest,
                port=port,
                protocol=protocol,
                action=action,
            )

        if not FirewallChangeRequest.objects.filter(status=FirewallChangeRequest.Status.PENDING).exists():
            for fw_name, source, dest, port, protocol, action, comment in PENDING_RULE_REQUESTS:
                change_request = FirewallChangeRequest.objects.create(
                    firewall=firewalls[fw_name],
                    change_type=FirewallChangeRequest.ChangeType.CREATE,
                    source_ip=source,
                    destination_ip=dest,
                    port=port,
                    protocol=protocol,
                    action=action,
                    request_comment=comment,
                    status=FirewallChangeRequest.Status.PENDING,
                )
                FirewallApprovalEvent.objects.create(
                    change_request=change_request,
                    event_type=FirewallApprovalEvent.EventType.REQUESTED,
                    comment=comment,
                )

        if not Alert.objects.exists():
            for index, (severity, status, title) in enumerate(ALERT_TITLES):
                Alert.objects.create(
                    title=title,
                    source="siem",
                    severity=severity,
                    status=status,
                    occurred_at=now - timedelta(days=index % 10, hours=index),
                )
            extra_days = 14
            for day in range(extra_days):
                Alert.objects.create(
                    title=f"IDS threshold warning (day -{day})",
                    source="ids",
                    severity="medium" if day % 2 else "high",
                    status="resolved" if day > 3 else "open",
                    occurred_at=now - timedelta(days=day, hours=3),
                )

        if not SecurityEvent.objects.exists():
            types = list(SecurityEvent.EventType.values)
            for day in range(7):
                for offset, event_type in enumerate(types):
                    SecurityEvent.objects.create(
                        event_type=event_type,
                        severity="high" if event_type in {"intrusion", "malware"} else "medium",
                        message=f"{event_type.replace('_', ' ')} event",
                        occurred_at=now - timedelta(days=day, hours=offset * 2),
                    )

        if not ResourceMetric.objects.exists():
            online = [s for s in servers if s.status == Server.Status.ONLINE]
            for hour in range(24):
                recorded = now - timedelta(hours=23 - hour)
                cpu_base = Decimal("40") + Decimal(hour % 7) * Decimal("3.5")
                ram_base = Decimal("55") + Decimal(hour % 5) * Decimal("2.8")
                for server in online:
                    ResourceMetric.objects.create(
                        metric=ResourceMetric.Metric.CPU,
                        value=min(Decimal("96.00"), cpu_base + Decimal(abs(hash(server.hostname)) % 9)),
                        recorded_at=recorded,
                        server=server,
                    )
                    ResourceMetric.objects.create(
                        metric=ResourceMetric.Metric.RAM,
                        value=min(Decimal("96.00"), ram_base + Decimal(abs(hash(server.hostname)) % 7)),
                        recorded_at=recorded,
                        server=server,
                    )

        User.objects.filter(is_active=True).update(last_login=now)

        self.stdout.write(self.style.SUCCESS("Dashboard demo data seeded."))
