from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.compute.api.v1.views import ServerViewSet

router = DefaultRouter()
router.register("servers", ServerViewSet, basename="servers")

urlpatterns = [
    path("", include(router.urls)),
]
