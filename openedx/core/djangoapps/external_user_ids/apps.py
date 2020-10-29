"""
External User ID Application Configuration
"""


from django.apps import AppConfig


class ExternalUserIDConfig(AppConfig):
    """
    Default configuration for the "openedx.core.djangoapps.credit" Django application.
    """
    name = 'openedx.core.djangoapps.external_user_ids'

    def ready(self):
        from . import signals  # pylint: disable=unused-import
