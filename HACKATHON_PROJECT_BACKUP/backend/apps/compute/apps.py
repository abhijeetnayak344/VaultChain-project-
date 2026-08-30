from django.apps import AppConfig


class ComputeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.compute"
    label = "compute"
    verbose_name = "Compute"
