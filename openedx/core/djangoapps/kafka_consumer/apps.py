"""App for consuming Kafka events. Comprises a management command for listening to a topic and supporting methods.
Likely temporary."""
from django.apps import AppConfig


class KafkaConsumerApp(AppConfig):
    name = 'openedx.core.djangoapps.kafka_consumer'
