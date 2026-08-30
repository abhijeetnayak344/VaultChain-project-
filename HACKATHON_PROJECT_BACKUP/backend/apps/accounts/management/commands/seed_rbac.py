from django.conf import settings
from django.core.management.base import BaseCommand

from apps.accounts.constants import PERMISSIONS, ROLE_PERMISSIONS, SUPER_ADMIN, SYSTEM_ROLES
from apps.accounts.models import Permission, Role, User


class Command(BaseCommand):
    help = "Seed system roles, permissions, and the bootstrap Super Admin."

    def handle(self, *args, **options):
        permissions = []
        for resource, action, description in PERMISSIONS:
            perm, _ = Permission.objects.update_or_create(
                resource=resource,
                action=action,
                defaults={"description": description, "codename": f"{resource}:{action}"},
            )
            permissions.append(perm)

        perm_by_code = {p.codename: p for p in Permission.objects.all()}

        for slug, name, description in SYSTEM_ROLES:
            role, _ = Role.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "description": description, "is_system": True},
            )
            grants = ROLE_PERMISSIONS.get(slug, ())
            if grants == "*":
                role.permissions.set(Permission.objects.all())
            else:
                role.permissions.set([perm_by_code[code] for code in grants if code in perm_by_code])

        email = (getattr(settings, "BOOTSTRAP_ADMIN_EMAIL", "") or "").strip().lower()
        password = getattr(settings, "BOOTSTRAP_ADMIN_PASSWORD", "") or ""
        if not email or not password:
            self.stdout.write("Bootstrap admin skipped (BOOTSTRAP_ADMIN_EMAIL/PASSWORD unset).")
            return

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": "SecureDC Super Admin",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        if created:
            user.set_password(password)
            user.save()
        super_role = Role.objects.get(slug=SUPER_ADMIN)
        user.roles.add(super_role)
        action = "created" if created else "ensured"
        self.stdout.write(self.style.SUCCESS(f"Bootstrap Super Admin {action}: {email}"))
