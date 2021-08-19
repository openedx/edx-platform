from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from confluent_kafka import SerializingProducer
from lms.djangoapps.arch_experiments.event_bus.producer import PRODUCER
from openedx_events.learning.data import (
    CourseEnrollmentData,
    UserData,
    CourseData,
    UserPersonalData,
)

from opaque_keys.edx.keys import CourseKey

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
            print(f"producing {i} event")
            user_personal_data = UserPersonalData(
                username="username", email="email", name="name"
            )
            user_data = UserData(id=1, is_active=True, pii=user_personal_data)
            # define Coursedata, which needs Coursekey, which needs opaque key
            course_id = "course-v1:edX+DemoX.1+2014"
            course_key = CourseKey.from_string(course_id)
            course_data = CourseData(
                course_key=course_key,
                display_name="display_name",
                start=datetime.now(),
                end=datetime.now(),
            )
            course_enrollment_data = CourseEnrollmentData(
                user=user_data,
                course=course_data,
                mode="mode",
                is_active=False,
                creation_date=datetime.now(),
                created_by=user_data,
            )

            PRODUCER.produce(
                topic=options["topic"],
                key=course_data,
                value=course_enrollment_data,
                on_delivery=acked,
            )
            PRODUCER.poll()
