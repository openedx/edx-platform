"""
OfflineMode application configuration
"""


from django.apps import AppConfig


class OfflineModeConfig(AppConfig):
    """
    Application Configuration for Offline Mode module.
    """

    name = 'openedx.features.offline_mode'

    def ready(self):
        """
        Import signals to register signal handlers
        """
        from . import signals, tasks  # pylint: disable=unused-import, import-outside-toplevel
