"""
Configuration for the email_marketing Django application.
"""
from django.apps import AppConfig


class EmailMarketingConfig(AppConfig):
    """
    Configuration class for the email_marketing Django application.
    """
    name = 'email_marketing'
    verbose_name = "Email Marketing"

    def ready(self):
        # Register the signal handlers.
        from . import signals  # pylint: disable=unused-variable
