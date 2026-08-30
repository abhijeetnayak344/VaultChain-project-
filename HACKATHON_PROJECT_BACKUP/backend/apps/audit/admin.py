from django.contrib import admin

from apps.audit.models import AuditLog, IntegrityAlert, IntegrityCheck


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "actor_email",
        "action",
        "resource_type",
        "chain_status",
        "verification_status",
        "ip_address",
    )
    list_filter = ("action", "resource_type", "chain_status", "verification_status")
    search_fields = ("actor_email", "resource_id", "ip_address", "action", "chain_tx_id")
    readonly_fields = (
        "id",
        "actor",
        "actor_email",
        "action",
        "resource_type",
        "resource_id",
        "ip_address",
        "details",
        "integrity_hash",
        "chain_tx_id",
        "chain_status",
        "verification_status",
        "created_at",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(IntegrityCheck)
class IntegrityCheckAdmin(admin.ModelAdmin):
    list_display = ("created_at", "result", "reason", "audit_log", "chain_tx_id")
    list_filter = ("result",)
    search_fields = ("current_hash", "blockchain_hash", "chain_tx_id")
    readonly_fields = (
        "id",
        "audit_log",
        "current_hash",
        "blockchain_hash",
        "stored_hash",
        "chain_tx_id",
        "result",
        "reason",
        "details",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(IntegrityAlert)
class IntegrityAlertAdmin(admin.ModelAdmin):
    list_display = ("created_at", "status", "reason", "audit_log")
    list_filter = ("status", "reason")
    readonly_fields = (
        "id",
        "audit_log",
        "integrity_check",
        "local_hash",
        "chain_hash",
        "chain_tx_id",
        "reason",
        "created_at",
        "updated_at",
    )
