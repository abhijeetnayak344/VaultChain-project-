from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import require_permission
from apps.audit.api.serializers import AuditLogSerializer, AuditSummarySerializer
from apps.audit.blockchain import chain_history, verify_log
from apps.audit.models import AuditLog
from apps.audit.services import summary


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    http_method_names = ["get", "head", "options"]

    def get_permissions(self):
        return [IsAuthenticated(), require_permission("audit:read")()]

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("actor")
        search = (self.request.query_params.get("search") or "").strip()
        action = (self.request.query_params.get("action") or "").strip()
        resource_type = (self.request.query_params.get("resource_type") or "").strip()
        resource_id = (self.request.query_params.get("resource_id") or "").strip()
        actor_email = (self.request.query_params.get("user") or "").strip()
        date_from = (self.request.query_params.get("date_from") or "").strip()
        date_to = (self.request.query_params.get("date_to") or "").strip()
        ip_address = (self.request.query_params.get("ip_address") or "").strip()
        chain_status = (self.request.query_params.get("chain_status") or "").strip()
        verification_status = (self.request.query_params.get("verification_status") or "").strip()

        if search:
            queryset = queryset.filter(
                Q(actor_email__icontains=search)
                | Q(action__icontains=search)
                | Q(resource_type__icontains=search)
                | Q(resource_id__icontains=search)
                | Q(ip_address__icontains=search)
            )
        if action:
            queryset = queryset.filter(action=action)
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)
        if actor_email:
            queryset = queryset.filter(actor_email__icontains=actor_email)
        if ip_address:
            queryset = queryset.filter(ip_address__icontains=ip_address)
        if chain_status:
            queryset = queryset.filter(chain_status=chain_status)
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset

    @action(detail=True, methods=["get"])
    def verify(self, request, pk=None):
        log = self.get_object()
        return Response(verify_log(log))

    @action(detail=True, methods=["get"], url_path="chain-history")
    def chain_history_view(self, request, pk=None):
        log = self.get_object()
        return Response(chain_history(str(log.id)))


class AuditSummaryView(APIView):
    def get_permissions(self):
        return [IsAuthenticated(), require_permission("audit:read")()]

    def get(self, request):
        serializer = AuditSummarySerializer(data=summary(hours=24))
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
