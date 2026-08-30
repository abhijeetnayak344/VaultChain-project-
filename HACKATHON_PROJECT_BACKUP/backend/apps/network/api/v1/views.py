from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import require_permission
from apps.network.api.serializers import (
    FirewallChangeRequestSerializer,
    FirewallRuleSerializer,
    FirewallSerializer,
    ReviewDecisionSerializer,
    annotate_firewall_queryset,
)
from apps.network.models import Firewall, FirewallChangeRequest, FirewallRule
from apps.network.services import decide_change


class FirewallViewSet(viewsets.ModelViewSet):
    serializer_class = FirewallSerializer
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), require_permission("firewall:read")()]
        if self.action == "create":
            return [IsAuthenticated(), require_permission("firewall:create")()]
        if self.action in ("partial_update", "update"):
            return [IsAuthenticated(), require_permission("firewall:update")()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = annotate_firewall_queryset(Firewall.objects.all())
        search = (self.request.query_params.get("search") or "").strip()
        status_filter = (self.request.query_params.get("status") or "").strip()
        vendor = (self.request.query_params.get("vendor") or "").strip()
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(vendor__icontains=search))
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if vendor:
            queryset = queryset.filter(vendor__iexact=vendor)
        return queryset


class FirewallRuleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FirewallRuleSerializer
    http_method_names = ["get", "head", "options"]

    def get_permissions(self):
        return [IsAuthenticated(), require_permission("firewall:read")()]

    def get_queryset(self):
        queryset = FirewallRule.objects.select_related("firewall")
        firewall = (self.request.query_params.get("firewall") or "").strip()
        if firewall:
            queryset = queryset.filter(firewall_id=firewall)
        return queryset


class FirewallChangeRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FirewallChangeRequestSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), require_permission("firewall:read")()]
        if self.action == "create":
            return [IsAuthenticated(), require_permission("firewall:request")()]
        if self.action == "approve":
            return [IsAuthenticated(), require_permission("firewall:approve")()]
        if self.action == "reject":
            return [IsAuthenticated(), require_permission("firewall:reject")()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = self._base_queryset()
        status_filter = (self.request.query_params.get("status") or "").strip()
        firewall = (self.request.query_params.get("firewall") or "").strip()
        change_type = (self.request.query_params.get("change_type") or "").strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if firewall:
            queryset = queryset.filter(firewall_id=firewall)
        if change_type:
            queryset = queryset.filter(change_type=change_type)
        return queryset

    def _base_queryset(self):
        return FirewallChangeRequest.objects.select_related(
            "firewall",
            "rule",
            "requested_by",
            "reviewed_by",
        ).prefetch_related("history__actor")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        serializer = ReviewDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decide_change(
            user=request.user,
            change_request=self.get_object(),
            approved=True,
            comment=serializer.validated_data.get("review_comment") or "",
        )
        return Response(self.get_serializer(self._base_queryset().get(pk=pk)).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        serializer = ReviewDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decide_change(
            user=request.user,
            change_request=self.get_object(),
            approved=False,
            comment=serializer.validated_data.get("review_comment") or "",
        )
        return Response(self.get_serializer(self._base_queryset().get(pk=pk)).data)
