from django.conf import settings
from confluent_kafka import KafkaError, KafkaException, Consumer, DeserializingConsumer
from lms.djangoapps.arch_experiments.event_bus.course_events import (
    COURSE_EVENT_KEY_DESERIALIZER,
    COURSE_EVENT_VALUE_DESERIALIZER,
)

consumer_settings = dict(settings.KAFKA_CONSUMER_CONF_BASE)
consumer_settings.update({'key.deserializer': COURSE_EVENT_KEY_DESERIALIZER,
                          'value.deserializer': COURSE_EVENT_VALUE_DESERIALIZER,
                          'auto.offset.reset': 'earliest'
                          }
                         )
CONSUMER = DeserializingConsumer(consumer_settings)
