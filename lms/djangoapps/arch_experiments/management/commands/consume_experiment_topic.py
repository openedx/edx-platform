from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from lms.djangoapps.arch_experiments.signals.handlers import ARCH_EXPERIMENTS_TOPIC, UnenrollSchema
import pulsar

from lms.djangoapps.arch_experiments.signals.handlers import UnenrollMessage

ARCH_EXPERIMENTS_CONSUMER = settings.PULSAR_CLIENT.subscribe(
    ARCH_EXPERIMENTS_TOPIC,
    settings.CONSUMER_GROUP_NAME,
    consumer_type=pulsar.ConsumerType.Shared,
    schema=UnenrollSchema()
)


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print("Starting to consume messages...")
        while True:
            try:
                msg = ARCH_EXPERIMENTS_CONSUMER.receive(500)
            except Exception as e:
                if (len(e.args) == 1) and ("TimeOut" in e.args[0]):
                    continue
                else:
                    raise
            try:
                print("Received message '{}' id='{}'".format(msg.data(), msg.message_id()))
                print(f"Type: '{type(msg.value())}', Content: '{msg.value()}'")
                # Acknowledge successful processing of the message
                ARCH_EXPERIMENTS_CONSUMER.acknowledge(msg)
            except:
                # Message failed to be processed
                ARCH_EXPERIMENTS_CONSUMER.negative_acknowledge(msg)
