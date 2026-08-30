from rest_framework import serializers

from apps.audit.models import AuditLog, IntegrityAlert, IntegrityCheck


class AuditLogSerializer(serializers.ModelSerializer):
    log_id = serializers.UUIDField(source="id", read_only=True)
    user = serializers.UUIDField(source="actor_id", read_only=True, allow_null=True)
    user_email = serializers.EmailField(source="actor_email", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            "log_id",
            "user",
            "user_email",
            "action",
            "timestamp",
            "ip_address",
            "resource_type",
            "resource_id",
            "details",
            "integrity_hash",
            "chain_tx_id",
            "chain_status",
            "verification_status",
        )
        read_only_fields = fields


class AuditSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    last_24h = serializers.IntegerField()
    logins_24h = serializers.IntegerField()
    approvals_24h = serializers.IntegerField()
    by_resource_type = serializers.ListField()
    by_action = serializers.ListField()


class BlockchainSummarySerializer(serializers.Serializer):
    critical_events = serializers.IntegerField()
    hashed = serializers.IntegerField()
    anchored = serializers.IntegerField()
    pending = serializers.IntegerField()
    failed = serializers.IntegerField()
    verified = serializers.IntegerField()
    alerts_open = serializers.IntegerField()
    alerts_acknowledged = serializers.IntegerField()
    alerts_total = serializers.IntegerField()
    checks = serializers.IntegerField()
    by_check_result = serializers.ListField()
    fabric_enabled = serializers.BooleanField()
    last_check_at = serializers.CharField(allow_null=True, allow_blank=True, required=False)


class BlockchainTransactionSerializer(serializers.ModelSerializer):
    log_id = serializers.UUIDField(source="id", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)
    user_email = serializers.EmailField(source="actor_email", read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            "log_id",
            "action",
            "resource_type",
            "resource_id",
            "user_email",
            "timestamp",
            "integrity_hash",
            "chain_tx_id",
            "chain_status",
            "verification_status",
        )
        read_only_fields = fields


class IntegrityCheckSerializer(serializers.ModelSerializer):
    log_id = serializers.UUIDField(source="audit_log_id", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = IntegrityCheck
        fields = (
            "id",
            "log_id",
            "current_hash",
            "blockchain_hash",
            "stored_hash",
            "chain_tx_id",
            "result",
            "reason",
            "details",
            "timestamp",
        )
        read_only_fields = fields


class IntegrityAlertSerializer(serializers.ModelSerializer):
    log_id = serializers.UUIDField(source="audit_log_id", read_only=True)
    action = serializers.CharField(source="audit_log.action", read_only=True)
    resource_type = serializers.CharField(source="audit_log.resource_type", read_only=True)
    resource_id = serializers.CharField(source="audit_log.resource_id", read_only=True)
    user_email = serializers.EmailField(source="audit_log.actor_email", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = IntegrityAlert
        fields = (
            "id",
            "log_id",
            "action",
            "resource_type",
            "resource_id",
            "user_email",
            "local_hash",
            "chain_hash",
            "chain_tx_id",
            "reason",
            "status",
            "timestamp",
        )
        read_only_fields = fields
