from django.conf import settings
from confluent_kafka import SerializingProducer

from lms.djangoapps.arch_experiments.event_bus.course_events import (
    COURSE_EVENT_KEY_SERIALIZER,
    COURSE_EVENT_VALUE_SERIALIZER,
)

producer_settings = dict(settings.KAFKA_PRODUCER_CONF_BASE)
producer_settings.update({'key.serializer': COURSE_EVENT_KEY_SERIALIZER,
                          'value.serializer': COURSE_EVENT_VALUE_SERIALIZER})
PRODUCER = SerializingProducer(producer_settings)
