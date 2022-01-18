"""
Management command for listening to license-manager events and logging them
"""

import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from confluent_kafka import KafkaError, KafkaException, DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringDeserializer
from openedx.core.djangoapps.kafka_consumer.consumers import getHandler


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Listen for license events from the event bus and log them. Only run on servers where KAFKA_ENABLED is true
    """
    help = """
    This starts a Kafka event consumer that listens to the specified topic and logs all messages it receives. Topic
    is required.

    example:
        manage.py ... consume_events -t license-event-prod

    """

    def add_arguments(self, parser):

        parser.add_argument(
            '-t', '--topic',
            nargs=1,
            required=True,
            help='Topic to consume'
        )

        parser.add_argument(
            '-g', '--group_id',
            nargs=1,
            required=True,
            help='Consumer group id'
        )

    def handle(self, *args, **options):
        if not settings.KAFKA_ENABLED:
            logger.error("Kafka not enabled")
            return
        try:
            KAFKA_SCHEMA_REGISTRY_CONFIG = {
                'url': settings.SCHEMA_REGISTRY_URL,
                'basic.auth.user.info': f"{settings.SCHEMA_REGISTRY_API_KEY}"
                f":{settings.SCHEMA_REGISTRY_API_SECRET}",
            }

            schema_registry_client = SchemaRegistryClient(KAFKA_SCHEMA_REGISTRY_CONFIG)

            topic = options['topic'][0]

            HandlerClass = getHandler(topic)

            consumer = DeserializingConsumer({
                'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVER,
                'group.id': options["group_id"][0],
                'key.deserializer': StringDeserializer('utf-8'),
                'value.deserializer': HandlerClass.getDeserializer(schema_registry_client),
                'auto.offset.reset': 'earliest',
                'sasl.mechanism': 'PLAIN',
                'security.protocol': 'SASL_SSL',
                'sasl.username': settings.KAFKA_API_KEY,
                'sasl.password': settings.KAFKA_API_SECRET,
            })

            try:
                consumer.subscribe([topic])

                while True:
                    msg = consumer.poll(timeout=1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            # End of partition event
                            logger.info(f"{msg.topic()} [{msg.partition()}] reached end at offset {msg.offset}")
                        elif msg.error():
                            logger.exception(msg.error())
                    else:
                        HandlerClass.handleMessage(msg)
            finally:
                # Close down consumer to commit final offsets.
                consumer.close()
        except Exception:
            logger.exception("Error consuming Kafka events")
