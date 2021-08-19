from django.apps import AppConfig


class EventBusExperimentConfig(AppConfig):
    name = 'lms.djangoapps.arch_experiments.event_bus'
    def read(self):
        from producer import PRODUCER
        from consumer import CONSUMER
