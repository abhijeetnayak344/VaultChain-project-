from django.urls import path

from apps.core.api.v1.views import ApiRootView, HealthView

urlpatterns = [
    path("", ApiRootView.as_view(), name="api-v1-root"),
    path("health/", HealthView.as_view(), name="api-v1-health"),
]
