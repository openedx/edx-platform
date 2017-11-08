
from django.apps import AppConfig


class ThemingConfig(AppConfig):
    name = 'openedx.core.djangoapps.theming'
    verbose_name = "Theming"

    def ready(self):
        # settings validations related to theming.
        from . import checks
