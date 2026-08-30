from rest_framework import serializers

from apps.compute.models import Server


class ServerSerializer(serializers.ModelSerializer):
    server_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Server
        fields = (
            "server_id",
            "code",
            "name",
            "hostname",
            "ip_address",
            "operating_system",
            "cpu_percent",
            "ram_percent",
            "storage_percent",
            "status",
            "location",
            "environment",
            "last_seen_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("server_id", "last_seen_at", "created_at", "updated_at")
        extra_kwargs = {
            "code": {"required": False, "allow_blank": True},
        }

    def validate_hostname(self, value):
        return value.strip().lower()

    def validate_code(self, value):
        return (value or "").strip().upper()

    def create(self, validated_data):
        if not validated_data.get("code"):
            validated_data.pop("code", None)
        return super().create(validated_data)
