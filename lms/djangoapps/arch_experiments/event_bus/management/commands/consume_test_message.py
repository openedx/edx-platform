
from django.core.management.base import BaseCommand
from confluent_kafka import KafkaException, KafkaError
from lms.djangoapps.arch_experiments.event_bus.consumer import CONSUMER

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--topic', default="test-topic")

    def handle(self, *args, **options):

        print("Starting to consume messages...")
        try:
            CONSUMER.subscribe([options["topic"]])

            while True:
                msg = CONSUMER.poll(timeout=1.0)
                if msg is None: continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        print('%% %s [%d] reached end at offset %d\n' %
                                         (msg.topic(), msg.partition(), msg.offset()))
                    elif msg.error():
                        raise KafkaException(msg.error())
                else:
                    course_data = msg.key()
                    course_enrollment_data = msg.value()
                    print(f"Received msg: {course_data}, {course_enrollment_data}")
        finally:
            # Close down consumer to commit final offsets.
            CONSUMER.close()
