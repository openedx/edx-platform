from common.djangoapps.student.signals.signals import UNENROLL_DONE
from django.dispatch import receiver
from pprint import pprint
from django.conf import settings
import json
from pulsar.schema import *
import _pulsar
from fastavro import schemaless_reader, schemaless_writer, parse_schema
import io
from lms.djangoapps.arch_experiments.models import BrokerOutboxMessage

ARCH_EXPERIMENTS_TOPIC = "arch_experiment_topic"

# Should be in Avro Spec Formated as a dict
# as consumed by `fastavro`
UNENROLL_SCHEMA_DEFINITION = {
    "name": "Unenroll",
    "type": "record",
    "fields": [
        {"name": "course", "type": "string"},
        {"name": "mode", "type": "string"},
        {"name": "user_id", "type": "int"},
        {"name": "extra_id", "type": "int", "default": 0},
    ],
}


CONSUMER_UNENROLL_SCHEMA_DEFINITION = {
    "name": "Unenroll",
    "type": "record",
    "fields": [
        {"name": "course", "type": "string"},
        {"name": "mode", "type": "string"},
        {"name": "user_id", "type": "int"},
    ],
}


class EdxAvroSchema(Schema):
    def __init__(self, avro_schema_definition: dict):
        super().__init__(None, _pulsar.SchemaType.AVRO, avro_schema_definition, "AVRO")
        self.parsed_schema = parse_schema(avro_schema_definition)

    def encode(self, obj):
        # Validate against schema.
        bytes_buffer = io.BytesIO()
        schemaless_writer(bytes_buffer, self.parsed_schema, obj)
        return bytes_buffer.getvalue()

    def decode(self, data):
        # Validate against schema
        bytes_buffer = io.BytesIO(data)
        d = schemaless_reader(bytes_buffer, self.parsed_schema)
        return d

    # Probably can be removed, need to write some tests to verify.
    def _validate_object_type(self, obj):
        return isinstance(obj, dict)


# Would be nice if this was created on-demand and in some sort of
# connection pool potentially.  Though it is thread safe and we
# may not need a connection pool.
# Instantiating here will cause it to fail as a part of start up
# rather than only failing if it doesn't work when we try to use it
# from within a view or a signal handler.
ARCH_EXPERIMENTS_PRODUCER = settings.PULSAR_CLIENT.create_producer(
    ARCH_EXPERIMENTS_TOPIC,
    schema=EdxAvroSchema(UNENROLL_SCHEMA_DEFINITION),
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
    #    ARCH_EXPERIMENTS_PRODUCER.send(
    #        content=enrollment_data,
    #        partition_key=str(course_enrollment.id),
    #    )

    # Do we want to do this on transaction.commit instead?
    BrokerOutboxMessage(
        serialized_key = str(course_enrollment.id).encode('utf-8'),
        serialized_value = EdxAvroSchema(UNENROLL_SCHEMA_DEFINITION).encode(enrollment_data),
        topic_name = ARCH_EXPERIMENTS_TOPIC,
    ).save()
