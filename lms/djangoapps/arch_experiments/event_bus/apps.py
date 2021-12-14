from django.apps import AppConfig
import logging
from .event_consumer import Consumer
from .kafka_serializers import LICENSE_EVENT_VALUE_DESERIALIZER
from confluent_kafka.serialization import StringDeserializer
from .events import LicenseTrackingEvent

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

class EventBusExperimentConfig(AppConfig):
    name = 'lms.djangoapps.arch_experiments.event_bus'
    def ready(self):

        def handle_license_event(license_event):
            logger.info(f"Received license event of type {license_event.key()}. License event data:"
                        f" {LicenseTrackingEvent.to_dict(license_event.value())}")

        def handle_license_event_error(license_event):
            logger.error(f"Error consuming license event: {license_event.error()}")

        license_event_consumer = Consumer(StringDeserializer('utf-8'), LICENSE_EVENT_VALUE_DESERIALIZER)
        license_event_consumer.listen("license_event", handle_license_event, handle_license_event_error)
