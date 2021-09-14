from django.apps import AppConfig


class ArchExperimentsConfig(AppConfig):
    name = 'lms.djangoapps.arch_experiments'

    def ready(self):
        from .signals import handlers
