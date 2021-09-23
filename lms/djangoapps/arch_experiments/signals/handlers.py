from common.djangoapps.student.signals.signals import UNENROLL_DONE
from django.dispatch import receiver
from pprint import pprint
from django.conf import settings
import json
from pulsar.schema import *
import _pulsar


ARCH_EXPERIMENTS_TOPIC = "arch_experiment_topic"


class UnenrollMessage(Record):
    user_id = Integer(required=True)
    course = String(required=True)
    mode = String(required=True)


class UnenrollSchema(Schema):
    json_schema_definition = {
        "$id": "https://edx.org/unenroll.schema.json",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Unenroll",
        "type": "object",
        "properties": {
            "user_id": {"type": "integer", "description": "The numeric id for the impacted user."},
            "course": {"type": "string", "description": "The course identifier."},
            "mode": {"type": "string", "description": "The mode they were enrolled in."},
        },
    }

    avro_schema_definition = {
        "name": "Unenroll",
        "type": "record",
        "fields": [
            {"name": "course", "type": "string"},
            {"name": "mode", "type": "string"},
            {"name": "user_id", "type": "int"},
#            {"name": "test_required", "type": "int", "default": 9}, # Added afterwards, required with default value.
#            {"name": "test_required2", "type": "int", "default": 9}, # Added afterwards, required with default value.
#            {"name": "test_optional", "type": ["int", "null"], "default": 9},
#            {"name": "test_optional2", "type": ["int", "null"], "default": 9}, # Added after the fact
#            {"name": "test_optional3", "type": ["int", "null"], "default": 9}, # Added after the fact
        ],
    }

    def __init__(self):
        # super().__init__(None, _pulsar.SchemaType.JSON, self.json_schema_definition, 'JSON')
        super().__init__(None, _pulsar.SchemaType.AVRO, self.avro_schema_definition, "AVRO")

    def encode(self, obj):
        # TODO: Validate against schema.
        return json.dumps(obj, indent=True).encode("utf-8")

    def decode(self, data):
        # TODO: Validate against schema
        return json.loads(data)

    def _validate_object_type(self, obj):
        return isinstance(obj, dict)


ARCH_EXPERIMENTS_PRODUCER = settings.PULSAR_CLIENT.create_producer(
    # ARCH_EXPERIMENTS_TOPIC, schema=AvroSchema(UnenrollMessage)
#    ARCH_EXPERIMENTS_TOPIC, schema=JsonSchema(UnenrollMessage)
    ARCH_EXPERIMENTS_TOPIC, schema=UnenrollSchema(),
)


@receiver(UNENROLL_DONE)
def transmit_unenrollment_to_event_bus(course_enrollment, **kwargs):
    print("=" * 80)
    print("=" * 80)
    pprint(kwargs)
    print("=" * 80)
    print("=" * 80)
    enrollment_data = dict(
        user_id=course_enrollment.user.id,
        course=str(course_enrollment.course.id),
        mode=course_enrollment.mode,
    )
    ARCH_EXPERIMENTS_PRODUCER.send(
        content=enrollment_data,
        partition_key=str(course_enrollment.id),
    )
