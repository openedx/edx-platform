from django.apps import AppConfig


class GenzFeaturesConfig(AppConfig):
    name = 'openedx.features.genz_features'

    def ready(self):
        from . import signals  # pylint: disable=unused-import
