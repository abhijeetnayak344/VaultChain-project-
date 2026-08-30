from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import require_permission
from apps.audit.api.serializers import (
    BlockchainSummarySerializer,
    BlockchainTransactionSerializer,
    IntegrityAlertSerializer,
    IntegrityCheckSerializer,
)
from apps.audit.models import AuditLog, IntegrityAlert, IntegrityCheck
from apps.audit.verification import blockchain_summary, set_alert_status, verify_and_record, verify_recent
from apps.core.pagination import StandardResultsSetPagination


class BlockchainReadMixin:
    def get_permissions(self):
        return [IsAuthenticated(), require_permission("audit:read")()]


class BlockchainAlertWriteMixin:
    def get_permissions(self):
        return [IsAuthenticated(), require_permission("audit:alert")()]


class BlockchainSummaryView(BlockchainReadMixin, APIView):
    def get(self, request):
        serializer = BlockchainSummarySerializer(data=blockchain_summary())
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class BlockchainTransactionView(BlockchainReadMixin, APIView):
    def get(self, request):
        queryset = AuditLog.objects.exclude(integrity_hash="").select_related("actor")
        search = (request.query_params.get("search") or "").strip()
        chain_status = (request.query_params.get("chain_status") or "").strip()
        verification_status = (request.query_params.get("verification_status") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(chain_tx_id__icontains=search)
                | Q(actor_email__icontains=search)
                | Q(action__icontains=search)
                | Q(resource_id__icontains=search)
            )
        if chain_status:
            queryset = queryset.filter(chain_status=chain_status)
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = BlockchainTransactionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class IntegrityCheckListView(BlockchainReadMixin, APIView):
    def get(self, request):
        queryset = IntegrityCheck.objects.select_related("audit_log")
        result = (request.query_params.get("result") or "").strip()
        log_id = (request.query_params.get("log_id") or "").strip()
        if result:
            queryset = queryset.filter(result=result)
        if log_id:
            queryset = queryset.filter(audit_log_id=log_id)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = IntegrityCheckSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class IntegrityCheckApiView(APIView):
    """Run current-hash vs blockchain-hash verification for one event or a recent scan."""

    def get_permissions(self):
        return [IsAuthenticated(), require_permission("audit:verify")()]

    def post(self, request):
        log_id = str(request.data.get("log_id") or "").strip()
        log_ids = request.data.get("log_ids") or []
        if log_id:
            log = AuditLog.objects.filter(pk=log_id).first()
            if log is None:
                return Response({"detail": "Audit event not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response(verify_and_record(log))
        if log_ids:
            return Response({"results": verify_recent(log_ids=log_ids)})
        limit = request.data.get("limit", 25)
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 25
        return Response({"results": verify_recent(limit=limit)})


class IntegrityAlertListView(BlockchainReadMixin, APIView):
    def get(self, request):
        queryset = IntegrityAlert.objects.select_related("audit_log")
        alert_status = (request.query_params.get("status") or "").strip()
        if alert_status:
            queryset = queryset.filter(status=alert_status)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = IntegrityAlertSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class IntegrityAlertAckView(BlockchainAlertWriteMixin, APIView):
    def post(self, request, pk):
        alert = IntegrityAlert.objects.filter(pk=pk).first()
        if alert is None:
            return Response({"detail": "Alert not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = IntegrityAlertSerializer(set_alert_status(alert, IntegrityAlert.Status.ACKNOWLEDGED))
        return Response(serializer.data)


class IntegrityAlertResolveView(BlockchainAlertWriteMixin, APIView):
    def post(self, request, pk):
        alert = IntegrityAlert.objects.filter(pk=pk).first()
        if alert is None:
            return Response({"detail": "Alert not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = IntegrityAlertSerializer(set_alert_status(alert, IntegrityAlert.Status.RESOLVED))
        return Response(serializer.data)
