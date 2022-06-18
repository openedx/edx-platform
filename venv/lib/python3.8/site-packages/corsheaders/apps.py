from django.apps import AppConfig
from django.core.checks import Tags, register

from corsheaders.checks import check_settings


class CorsHeadersAppConfig(AppConfig):
    name = "corsheaders"
    verbose_name = "django-cors-headers"

    def ready(self) -> None:
        register(Tags.security)(check_settings)
