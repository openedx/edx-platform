from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from confluent_kafka import SerializingProducer
from lms.djangoapps.arch_experiments.event_bus.course_events import (
    Course,
    CourseEventKey,
    CourseEnrollmentEventValue,
)
from lms.djangoapps.arch_experiments.event_bus.producer import PRODUCER

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--topic', default="test-topic")
        parser.add_argument('--student', default="12345")

    def handle(self, *args, **options):
        def acked(err, msg):
            if err is not None:
                print(f"Failed to deliver message: {msg}: {err}")
            else:
                print(f"Message produced with key {msg.key()} and value {msg.value()}")


        print("Producing test messages")

        for i in range(10):
            course = Course(f"edX+{i}", f"Introduction to the number {i}", "edX")
            event_key = CourseEventKey(course.course_key)
            event_value = CourseEnrollmentEventValue(course, options["student"], i%2 == 0)
            PRODUCER.produce(
                topic=options["topic"],
                key=event_key,
                value=event_value,
                on_delivery=acked,
            )
            PRODUCER.poll()
