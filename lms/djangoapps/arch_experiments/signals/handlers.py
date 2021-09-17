from common.djangoapps.student.signals.signals import UNENROLL_DONE
from django.dispatch import receiver
from pprint import pprint
from django.conf import settings
import json
from pulsar import schema


ARCH_EXPERIMENTS_TOPIC = "arch_experiment_topic"


class UnenrollSchema:
    @classmethod
    def schema(cls):
        _schema = {
            "name": "Unenrollment",
            "type": "record",
            "fields": [
                {"name": "user_id", "type": "long"},
                {"name": "course", "type": "string"},
                {"name": "mode", "type": "string"},
            ],
        }

        return _schema
        #return json.dumps(_schema)
        #return json.dumps({"type": "AVRO", "schema": json.dumps(_schema), "properties": {}})
        #return {"name": "test_schema", "type": "", "schema": json.dumps(_schema), "properties": {}}

class AvroSchema(schema.Schema):
    def __init__(self, schema: dict):
        super().__init__(


ARCH_EXPERIMENTS_PRODUCER = settings.PULSAR_CLIENT.create_producer(
    ARCH_EXPERIMENTS_TOPIC, schema=schema.AvroSchema(UnenrollSchema)
)


@receiver(UNENROLL_DONE)
def transmit_unenrollment_to_event_bus(course_enrollment, **kwargs):
    print("=" * 80)
    print("=" * 80)
    pprint(kwargs)
    print("=" * 80)
    print("=" * 80)
    enrollment_data = {
        "user_id": course_enrollment.user.id,
        "course": str(course_enrollment.course.id),
        "mode": course_enrollment.mode,
    }
    ARCH_EXPERIMENTS_PRODUCER.send(
        content=enrollment_data,
        partition_key=str(course_enrollment.id),
    )
