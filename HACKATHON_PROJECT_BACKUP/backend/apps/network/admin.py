from django.contrib import admin

from apps.network.models import Firewall, FirewallApprovalEvent, FirewallChangeRequest, FirewallRule


@admin.register(Firewall)
class FirewallAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "status")
    list_filter = ("status", "vendor")
    search_fields = ("name", "vendor")


@admin.register(FirewallRule)
class FirewallRuleAdmin(admin.ModelAdmin):
    list_display = ("firewall", "action", "protocol", "port", "source_ip", "destination_ip")
    list_filter = ("action", "protocol", "firewall")
    search_fields = ("source_ip", "destination_ip")


class FirewallApprovalEventInline(admin.TabularInline):
    model = FirewallApprovalEvent
    extra = 0
    readonly_fields = ("event_type", "actor", "comment", "created_at")
    can_delete = False


@admin.register(FirewallChangeRequest)
class FirewallChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "firewall", "change_type", "status", "requested_by", "requested_at")
    list_filter = ("status", "change_type")
    search_fields = ("firewall__name", "source_ip", "destination_ip")
    inlines = [FirewallApprovalEventInline]
    readonly_fields = ("requested_at", "reviewed_at")
