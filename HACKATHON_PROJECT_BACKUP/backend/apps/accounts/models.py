import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.constants import SUPER_ADMIN


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class Permission(models.Model):
    resource = models.CharField(max_length=64)
    action = models.CharField(max_length=64)
    codename = models.CharField(max_length=129, unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_permission"
        ordering = ["resource", "action"]
        constraints = [
            models.UniqueConstraint(fields=["resource", "action"], name="uniq_permission_resource_action"),
        ]

    def save(self, *args, **kwargs):
        self.codename = f"{self.resource}:{self.action}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.codename


class Role(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=False)
    permissions = models.ManyToManyField(Permission, related_name="roles", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_role"
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(default=timezone.now)
    roles = models.ManyToManyField(Role, related_name="users", blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "accounts_user"
        ordering = ["email"]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower().strip()
        super().save(*args, **kwargs)

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def is_platform_super_admin(self):
        if self.is_superuser:
            return True
        return self.roles.filter(slug=SUPER_ADMIN).exists()

    def permission_codenames(self):
        if self.is_platform_super_admin():
            return list(Permission.objects.values_list("codename", flat=True))
        return list(
            Permission.objects.filter(roles__users=self)
            .distinct()
            .values_list("codename", flat=True)
        )

    def has_perm_codename(self, codename):
        if not self.is_active or self.is_locked():
            return False
        if self.is_platform_super_admin():
            return True
        return self.roles.filter(permissions__codename=codename).exists()

    def has_role(self, slug):
        return self.roles.filter(slug=slug).exists()
