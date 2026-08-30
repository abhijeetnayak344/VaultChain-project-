from django.db import connection
from django.db.utils import OperationalError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.serializers import HealthSerializer


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        database = "ok"
        try:
            connection.ensure_connection()
        except OperationalError:
            database = "unavailable"

        payload = {
            "status": "ok" if database == "ok" else "degraded",
            "service": "aicte-securedc-api",
            "version": "v1",
            "database": database,
        }
        serializer = HealthSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class ApiRootView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(
            {
                "name": "AICTE SecureDC API",
                "version": "v1",
                "status": "ready",
                "resources": {
                    "health": request.build_absolute_uri("health/"),
                    "register": request.build_absolute_uri("auth/register/"),
                    "login": request.build_absolute_uri("auth/login/"),
                    "refresh": request.build_absolute_uri("auth/refresh/"),
                    "logout": request.build_absolute_uri("auth/logout/"),
                    "me": request.build_absolute_uri("auth/me/"),
                    "users": request.build_absolute_uri("users/"),
                    "roles": request.build_absolute_uri("roles/"),
                    "permissions": request.build_absolute_uri("permissions/"),
                    "dashboard_summary": request.build_absolute_uri("dashboard/summary/"),
                    "dashboard_cpu": request.build_absolute_uri("dashboard/charts/cpu/"),
                    "dashboard_ram": request.build_absolute_uri("dashboard/charts/ram/"),
                    "dashboard_security_events": request.build_absolute_uri("dashboard/charts/security-events/"),
                    "dashboard_alerts": request.build_absolute_uri("dashboard/charts/alerts/"),
                    "servers": request.build_absolute_uri("servers/"),
                    "firewalls": request.build_absolute_uri("firewalls/"),
                    "firewall_rules": request.build_absolute_uri("firewall-rules/"),
                    "firewall_change_requests": request.build_absolute_uri("firewall-change-requests/"),
                    "audit_logs": request.build_absolute_uri("audit/logs/"),
                    "audit_summary": request.build_absolute_uri("audit/summary/"),
                    "audit_verify": request.build_absolute_uri("audit/logs/{id}/verify/"),
                    "audit_chain_history": request.build_absolute_uri("audit/logs/{id}/chain-history/"),
                    "blockchain_summary": request.build_absolute_uri("blockchain/summary/"),
                    "blockchain_verify": request.build_absolute_uri("blockchain/verify/"),
                    "blockchain_transactions": request.build_absolute_uri("blockchain/transactions/"),
                    "blockchain_alerts": request.build_absolute_uri("blockchain/alerts/"),
                    "blockchain_checks": request.build_absolute_uri("blockchain/checks/"),
                },
            }
        )
