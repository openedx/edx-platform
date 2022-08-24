from django.apps import AppConfig


class GenPlusBadgesConfig(AppConfig):
    name = 'openedx.features.genplus_features.genplus_badges'

    def ready(self):
        from . import signals  # pylint: disable=unused-import
