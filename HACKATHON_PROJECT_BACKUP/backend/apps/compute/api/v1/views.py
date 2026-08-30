from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import require_permission
from apps.compute.api.serializers import ServerSerializer
from apps.compute.models import Server


class ServerViewSet(viewsets.ModelViewSet):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), require_permission("server:read")()]
        if self.action == "create":
            return [IsAuthenticated(), require_permission("server:create")()]
        if self.action in ("partial_update", "update"):
            return [IsAuthenticated(), require_permission("server:update")()]
        if self.action == "destroy":
            return [IsAuthenticated(), require_permission("server:delete")()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Server.objects.all()
        search = (self.request.query_params.get("search") or "").strip()
        status = (self.request.query_params.get("status") or "").strip()
        location = (self.request.query_params.get("location") or "").strip()
        operating_system = (self.request.query_params.get("operating_system") or "").strip()

        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(hostname__icontains=search)
                | Q(ip_address__icontains=search)
                | Q(location__icontains=search)
                | Q(operating_system__icontains=search)
            )
        if status:
            queryset = queryset.filter(status=status)
        if location:
            queryset = queryset.filter(location__iexact=location)
        if operating_system:
            queryset = queryset.filter(operating_system__icontains=operating_system)
        return queryset
