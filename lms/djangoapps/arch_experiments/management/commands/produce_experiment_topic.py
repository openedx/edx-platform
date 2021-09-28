from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
import pulsar

from lms.djangoapps.arch_experiments.signals.handlers import (
    EdxAvroSchema,
    UNENROLL_SCHEMA_DEFINITION,
    ARCH_EXPERIMENTS_TOPIC,
    ARCH_EXPERIMENTS_PRODUCER,
)
from lms.djangoapps.arch_experiments.models import BrokerOutboxMessage

TOPICS_TO_PRODUCERS = {
    ARCH_EXPERIMENTS_TOPIC: ARCH_EXPERIMENTS_PRODUCER,
}

TOPICS_TO_SCHEMA = {
    ARCH_EXPERIMENTS_TOPIC: EdxAvroSchema(UNENROLL_SCHEMA_DEFINITION),
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print("Starting to produce messages from the outbox...")

        while True:
            for message in BrokerOutboxMessage.objects.all():
                print(f"Processing {message}")
                with transaction.atomic():
                    producer = TOPICS_TO_PRODUCERS[message.topic_name]
                    producer.send(
                        partition_key=message.serialized_key.decode('utf-8'),
                        content=TOPICS_TO_SCHEMA[message.topic_name].decode(message.serialized_value),
                        event_timestamp=int(message.created.timestamp() * 1000),  # timestamp in milliseconds
                    )

                    # If the delete fails, the message may get sent more than once.
                    message.delete()
