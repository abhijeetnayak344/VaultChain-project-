from django.contrib import admin

from apps.compute.models import Server


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "hostname",
        "ip_address",
        "status",
        "location",
        "cpu_percent",
        "ram_percent",
        "storage_percent",
    )
    list_filter = ("status", "location", "operating_system", "environment")
    search_fields = ("code", "name", "hostname", "ip_address", "location")
