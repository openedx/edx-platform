from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from lms.djangoapps.arch_experiments.signals.handlers import ARCH_EXPERIMENTS_TOPIC
import pulsar

ARCH_EXPERIMENTS_CONSUMER = settings.PULSAR_CLIENT.subscribe(
    ARCH_EXPERIMENTS_TOPIC,
    settings.CONSUMER_GROUP_NAME,
    consumer_type=pulsar.ConsumerType.Shared,
)
class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print("Starting to consume messages...")
        while True:
            msg = ARCH_EXPERIMENTS_CONSUMER.receive()
            try:
                print("Received message '{}' id='{}'".format(msg.data(), msg.message_id()))
                # Acknowledge successful processing of the message
                ARCH_EXPERIMENTS_CONSUMER.acknowledge(msg)
            except:
                # Message failed to be processed
                ARCH_EXPERIMENTS_CONSUMER.negative_acknowledge(msg)

