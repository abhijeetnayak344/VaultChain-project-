from django.core.management.base import BaseCommand

from apps.audit.blockchain import event_hash
from apps.audit.models import AuditLog


class Command(BaseCommand):
    help = "Compute SHA-256 integrity hashes for existing audit rows that have none."

    def handle(self, *args, **options):
        updated = 0
        for log in AuditLog.objects.filter(integrity_hash="").iterator():
            AuditLog.objects.filter(pk=log.pk).update(
                integrity_hash=event_hash(log),
                verification_status="unverified",
            )
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Hashed {updated} audit events."))
