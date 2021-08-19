
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
                    course_key = msg.key().course_key
                    course_event = msg.value()
                    course = course_event.course
                    is_enroll = course_event.is_enroll
                    student = course_event.user_id

                    print(f"Course key: {course_key}")
                    print(f"{ 'Enrolled' if is_enroll else 'Unenrolled' } student {student} from {course.formatted_title()}")
        finally:
            # Close down consumer to commit final offsets.
            CONSUMER.close()
