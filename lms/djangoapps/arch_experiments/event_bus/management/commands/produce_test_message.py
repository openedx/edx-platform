from django.core.management.base import BaseCommand
from lms.djangoapps.arch_experiments.event_bus.events import (
    Course,
    CourseEventKey,
    CourseEnrollmentEventValue,
)
from lms.djangoapps.arch_experiments.event_bus.producer import ProducerFactory
from lms.djangoapps.arch_experiments.event_bus.kafka_serializers import (
COURSE_EVENT_VALUE_SERIALIZER,
COURSE_EVENT_KEY_SERIALIZER,
)

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--topic', default="test-topic")
        parser.add_argument('--student', default="12345")

    def handle(self, *args, **options):
        test_event_producer = ProducerFactory.get_or_create_event_producer("test", COURSE_EVENT_KEY_SERIALIZER,
                                                                           COURSE_EVENT_VALUE_SERIALIZER)
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

            test_event_producer.produce(
                topic=options["topic"],
                key=event_key,
                value=event_value,
                on_delivery=acked,
            )
            test_event_producer.poll()
