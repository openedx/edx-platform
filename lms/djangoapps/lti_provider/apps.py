"""
Configuration for the lti_provider Django application.
"""
from django.apps import AppConfig


class LtiProviderConfig(AppConfig):
    """
    Configuration class for the lti_provider Django application.
    """
    name = 'lti_provider'
    verbose_name = "LTI Provider"

    def ready(self):
        # Import the tasks module to ensure that signal handlers are registered.
        from . import signals  # pylint: disable=unused-variable
