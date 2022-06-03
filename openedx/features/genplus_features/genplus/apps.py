from django.apps import AppConfig


class GenPlusFeaturesConfig(AppConfig):
    name = 'openedx.features.genplus_features.genplus'

    def ready(self):
        #from . import signals  # pylint: disable=unused-import
        pass
