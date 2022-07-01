"""
Management command for listening to license-manager events and logging them
"""

import logging

from confluent_kafka import DeserializingConsumer, KafkaError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringDeserializer
from django.conf import settings
from django.core.management.base import BaseCommand
from edx_toggles.toggles import SettingToggle

from openedx.core.djangoapps.kafka_consumer.consumers import getHandler

logger = logging.getLogger(__name__)

# .. toggle_name: KAFKA_CONSUMERS_ENABLED
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: Enables the ability to listen and process events from the Kafka event bus
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2022-01-31
# .. toggle_tickets: https://openedx.atlassian.net/browse/ARCHBOM-1992
KAFKA_CONSUMERS_ENABLED = SettingToggle('KAFKA_CONSUMERS_ENABLED', default=False)

CONSUMER_POLL_TIMEOUT = getattr(settings, 'CONSUMER_POLL_TIMEOUT', 1.0)


class Command(BaseCommand):
    """
    Listen for events from the event bus and log them. Only run on servers where KAFKA_CONSUMERS_ENABLED is true
    """
    help = """
    This starts a Kafka event consumer that listens to the specified topic and logs all messages it receives. Topic
    is required.

    example:
        manage.py ... consume_events -t license-event-prod -g license-event-consumers

    # TODO (EventBus): Add pointer to relevant future docs around topics and consumer groups, and potentially
    update example topic and group names to follow any future naming conventions.

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
        if not KAFKA_CONSUMERS_ENABLED.is_enabled():
            logger.error("Kafka consumers not enabled")
            return
        try:
            KAFKA_SCHEMA_REGISTRY_CONFIG = {
                'url': settings.SCHEMA_REGISTRY_URL,
                'basic.auth.user.info': f"{settings.SCHEMA_REGISTRY_API_KEY}:{settings.SCHEMA_REGISTRY_API_SECRET}",
            }

            schema_registry_client = SchemaRegistryClient(KAFKA_SCHEMA_REGISTRY_CONFIG)

            topic = options['topic'][0]

            HandlerClass = getHandler(topic)

            # TODO (EventBus):
            #  1. generalize configurations to allow connection to local Kafka clusters without SSL
            #  2. Reevaluate if all consumers should listen for the earliest unprocessed offset (auto.offset.reset)

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

                # TODO (EventBus):
                # 1. Is there an elegant way to exit the loop?
                # 2. Determine if there are other errors that shouldn't kill the entire loop
                while True:
                    msg = consumer.poll(timeout=CONSUMER_POLL_TIMEOUT)
                    if msg is None:
                        continue
                    if msg.error():
                        # TODO (EventBus): iterate on error handling with retry and dead-letter queue topics
                        if msg.error().code() == KafkaError._PARTITION_EOF:  # pylint: disable=protected-access
                            # End of partition event
                            logger.info(f"{msg.topic()} [{msg.partition()}] reached end at offset {msg.offset}")
                        elif msg.error():
                            logger.exception(msg.error())
                        continue
                    HandlerClass.handleMessage(msg)
            finally:
                # Close down consumer to commit final offsets.
                consumer.close()
                logger.info("Committing final offsets")
        except Exception:  # pylint: disable=broad-except
            logger.exception("Error consuming Kafka events")
