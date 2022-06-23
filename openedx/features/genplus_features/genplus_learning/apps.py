from django.apps import AppConfig


class GenPlusLearningConfig(AppConfig):
    name = 'openedx.features.genplus_features.genplus_learning'

    def ready(self):
        from . import signals  # pylint: disable=unused-import
