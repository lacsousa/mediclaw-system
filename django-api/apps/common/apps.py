from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"

    def ready(self):
        from django.conf import settings

        from apps.common.logging_config import configure_structlog

        configure_structlog(debug=settings.DEBUG)
