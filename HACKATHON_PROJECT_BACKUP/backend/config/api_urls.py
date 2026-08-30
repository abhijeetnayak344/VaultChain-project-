"""Versioned API mount. Feature apps register under api/v1/ in later phases."""

from django.urls import include, path

urlpatterns = [
    path("v1/", include("apps.core.api.v1.urls")),
    path("v1/", include("apps.accounts.api.v1.urls")),
    path("v1/", include("apps.monitoring.api.v1.urls")),
    path("v1/", include("apps.compute.api.v1.urls")),
    path("v1/", include("apps.network.api.v1.urls")),
    path("v1/", include("apps.audit.api.v1.urls")),
]
