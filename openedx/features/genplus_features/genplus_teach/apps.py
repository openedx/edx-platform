from django.apps import AppConfig


class GenPlusTeachConfig(AppConfig):
    name = 'openedx.features.genplus_features.genplus_teach'

    def ready(self):
        #from . import signals  # pylint: disable=unused-import
        pass
