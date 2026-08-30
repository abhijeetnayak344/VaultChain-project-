from django.urls import path

from apps.audit.api.v1.blockchain_views import (
    BlockchainSummaryView,
    BlockchainTransactionView,
    IntegrityAlertAckView,
    IntegrityAlertListView,
    IntegrityAlertResolveView,
    IntegrityCheckApiView,
    IntegrityCheckListView,
)
from apps.audit.api.v1.views import AuditLogViewSet, AuditSummaryView

urlpatterns = [
    path("audit/summary/", AuditSummaryView.as_view(), name="audit-summary"),
    path("audit/logs/", AuditLogViewSet.as_view({"get": "list"}), name="audit-logs-list"),
    path("audit/logs/<uuid:pk>/", AuditLogViewSet.as_view({"get": "retrieve"}), name="audit-logs-detail"),
    path("audit/logs/<uuid:pk>/verify/", AuditLogViewSet.as_view({"get": "verify"}), name="audit-logs-verify"),
    path(
        "audit/logs/<uuid:pk>/chain-history/",
        AuditLogViewSet.as_view({"get": "chain_history_view"}),
        name="audit-logs-chain-history",
    ),
    path("blockchain/summary/", BlockchainSummaryView.as_view(), name="blockchain-summary"),
    path("blockchain/transactions/", BlockchainTransactionView.as_view(), name="blockchain-transactions"),
    path("blockchain/checks/", IntegrityCheckListView.as_view(), name="blockchain-checks"),
    path("blockchain/verify/", IntegrityCheckApiView.as_view(), name="blockchain-verify"),
    path("blockchain/alerts/", IntegrityAlertListView.as_view(), name="blockchain-alerts"),
    path(
        "blockchain/alerts/<uuid:pk>/acknowledge/",
        IntegrityAlertAckView.as_view(),
        name="blockchain-alerts-ack",
    ),
    path(
        "blockchain/alerts/<uuid:pk>/resolve/",
        IntegrityAlertResolveView.as_view(),
        name="blockchain-alerts-resolve",
    ),
]
