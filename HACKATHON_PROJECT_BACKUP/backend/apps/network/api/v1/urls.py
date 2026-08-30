from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.network.api.v1.views import (
    FirewallChangeRequestViewSet,
    FirewallRuleViewSet,
    FirewallViewSet,
)

router = DefaultRouter()
router.register("firewalls", FirewallViewSet, basename="firewalls")
router.register("firewall-rules", FirewallRuleViewSet, basename="firewall-rules")
router.register("firewall-change-requests", FirewallChangeRequestViewSet, basename="firewall-change-requests")

urlpatterns = [
    path("", include(router.urls)),
]
