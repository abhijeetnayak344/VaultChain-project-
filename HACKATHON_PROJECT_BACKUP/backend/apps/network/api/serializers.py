import ipaddress

from django.db.models import Count, Q
from rest_framework import serializers

from apps.network.models import (
    Firewall,
    FirewallApprovalEvent,
    FirewallChangeRequest,
    FirewallRule,
)
from apps.network.services import submit_change


def validate_ip_target(value):
    raw = (value or "").strip()
    if not raw:
        raise serializers.ValidationError("This field is required.")
    if raw.lower() == "any":
        return "any"
    try:
        if "/" in raw:
            ipaddress.ip_network(raw, strict=False)
        else:
            ipaddress.ip_address(raw)
    except ValueError as exc:
        raise serializers.ValidationError("Enter a valid IP address, CIDR, or 'any'.") from exc
    return raw


class FirewallSerializer(serializers.ModelSerializer):
    firewall_id = serializers.UUIDField(source="id", read_only=True)
    rule_count = serializers.SerializerMethodField()
    pending_request_count = serializers.SerializerMethodField()

    class Meta:
        model = Firewall
        fields = (
            "firewall_id",
            "name",
            "vendor",
            "status",
            "rule_count",
            "pending_request_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("firewall_id", "rule_count", "pending_request_count", "created_at", "updated_at")

    def get_rule_count(self, obj):
        if hasattr(obj, "rule_count"):
            return obj.rule_count
        return obj.rules.count() if obj.pk else 0

    def get_pending_request_count(self, obj):
        if hasattr(obj, "pending_request_count"):
            return obj.pending_request_count
        if not obj.pk:
            return 0
        return obj.change_requests.filter(status=FirewallChangeRequest.Status.PENDING).count()


class FirewallRuleSerializer(serializers.ModelSerializer):
    rule_id = serializers.UUIDField(source="id", read_only=True)
    firewall = serializers.UUIDField(source="firewall_id", read_only=True)
    firewall_name = serializers.CharField(source="firewall.name", read_only=True)

    class Meta:
        model = FirewallRule
        fields = (
            "rule_id",
            "firewall",
            "firewall_name",
            "source_ip",
            "destination_ip",
            "port",
            "protocol",
            "action",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class FirewallApprovalEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()

    class Meta:
        model = FirewallApprovalEvent
        fields = ("id", "event_type", "actor_email", "comment", "created_at")
        read_only_fields = fields

    def get_actor_email(self, obj):
        return obj.actor.email if obj.actor else None


class FirewallChangeRequestSerializer(serializers.ModelSerializer):
    request_id = serializers.UUIDField(source="id", read_only=True)
    firewall = serializers.PrimaryKeyRelatedField(queryset=Firewall.objects.all())
    firewall_name = serializers.CharField(source="firewall.name", read_only=True)
    rule = serializers.PrimaryKeyRelatedField(queryset=FirewallRule.objects.all(), required=False, allow_null=True)
    requested_by_email = serializers.SerializerMethodField()
    reviewed_by_email = serializers.SerializerMethodField()
    history = FirewallApprovalEventSerializer(many=True, read_only=True)

    class Meta:
        model = FirewallChangeRequest
        fields = (
            "request_id",
            "firewall",
            "firewall_name",
            "rule",
            "change_type",
            "source_ip",
            "destination_ip",
            "port",
            "protocol",
            "action",
            "status",
            "request_comment",
            "review_comment",
            "requested_by_email",
            "reviewed_by_email",
            "requested_at",
            "reviewed_at",
            "history",
        )
        read_only_fields = (
            "request_id",
            "firewall_name",
            "status",
            "review_comment",
            "requested_by_email",
            "reviewed_by_email",
            "requested_at",
            "reviewed_at",
            "history",
        )
        extra_kwargs = {
            "source_ip": {"required": False, "allow_blank": True},
            "destination_ip": {"required": False, "allow_blank": True},
            "protocol": {"required": False, "allow_blank": True},
            "action": {"required": False, "allow_blank": True},
            "port": {"required": False, "allow_null": True},
            "request_comment": {"required": False, "allow_blank": True},
        }

    def get_requested_by_email(self, obj):
        return obj.requested_by.email if obj.requested_by else None

    def get_reviewed_by_email(self, obj):
        return obj.reviewed_by.email if obj.reviewed_by else None

    def validate_source_ip(self, value):
        if (self.initial_data.get("change_type") or "") == FirewallChangeRequest.ChangeType.DELETE:
            return value
        return validate_ip_target(value)

    def validate_destination_ip(self, value):
        if (self.initial_data.get("change_type") or "") == FirewallChangeRequest.ChangeType.DELETE:
            return value
        return validate_ip_target(value)

    def validate(self, attrs):
        change_type = attrs.get("change_type")
        protocol = (attrs.get("protocol") or "").lower()
        port = attrs.get("port")
        if change_type != FirewallChangeRequest.ChangeType.DELETE:
            if not attrs.get("protocol") or not attrs.get("action"):
                raise serializers.ValidationError("Protocol and action are required for add and edit requests.")
            if protocol in {FirewallRule.Protocol.TCP, FirewallRule.Protocol.UDP} and port is None:
                raise serializers.ValidationError({"port": "Port is required for TCP and UDP."})
            if protocol == FirewallRule.Protocol.ICMP and port is not None:
                raise serializers.ValidationError({"port": "ICMP rules cannot specify a port."})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return submit_change(
            user=request.user,
            firewall=validated_data["firewall"],
            change_type=validated_data["change_type"],
            rule=validated_data.get("rule"),
            fields={
                "source_ip": validated_data.get("source_ip"),
                "destination_ip": validated_data.get("destination_ip"),
                "port": validated_data.get("port"),
                "protocol": validated_data.get("protocol"),
                "action": validated_data.get("action"),
            },
            comment=validated_data.get("request_comment") or "",
        )


class ReviewDecisionSerializer(serializers.Serializer):
    review_comment = serializers.CharField(required=False, allow_blank=True, max_length=255)


def annotate_firewall_queryset(queryset):
    return queryset.annotate(
        rule_count=Count("rules", distinct=True),
        pending_request_count=Count(
            "change_requests",
            filter=Q(change_requests__status=FirewallChangeRequest.Status.PENDING),
            distinct=True,
        ),
    )
