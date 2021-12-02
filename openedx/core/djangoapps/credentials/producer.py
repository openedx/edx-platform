from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from uuid import uuid4
from django.conf import settings


grade_change_schema_string = """
    {
        "namespace": "djangoapps.credentials.producer",
        "name": "GradeChangeEvent",
        "type": "record",
        "fields": [
            {"name": "username", "type": "string"},
            {"name":"course_run", "type": "string"},
            {"name":"letter_grade", "type": ["string", "null"], "default": "null"},
            {"name":"percent_grade", "type": ["float", "null"], "default": "null"},
            {"name":"verified", "type": "boolean"}
        ]
    }
"""

class GradeChangeEvent:
    def __init__(self, *args, **kwargs):
        self.course_run = kwargs['course_run']
        self.username = kwargs['username']
        self.letter_grade = kwargs['letter_grade']
        self.percent_grade = kwargs['percent_grade']
        self.verified = kwargs['verified']

    @staticmethod
    def from_dict(obj, ctx):
        return GradeChangeEvent(obj)

    @staticmethod
    def to_dict(grade_change_event, ctx):
        return {
            "course_run": grade_change_event.course_run,
            "username": grade_change_event.username,
            "letter_grade": grade_change_event.letter_grade,
            "percent_grade": grade_change_event.percent_grade,
            "verified": grade_change_event.verified,
        }


SCHEMA_REGISTRY_CLIENT = SchemaRegistryClient({
    'url': settings.SCHEMA_REGISTRY_URL,
})
GRADE_CHANGE_EVENT_SERIALIZER = AvroSerializer(schema_str=grade_change_schema_string, schema_registry_client=SCHEMA_REGISTRY_CLIENT,
                                               to_dict = GradeChangeEvent.to_dict)

producer_settings = dict(settings.KAFKA_PRODUCER_CONF_BASE)
producer_settings.update({'key.serializer': StringSerializer('utf-8'),
                          'value.serializer': GRADE_CHANGE_EVENT_SERIALIZER})
GRADE_CHANGE_EVENT_PRODUCER = SerializingProducer(producer_settings)

def produce_grade_change_event(user, course_run_key, letter_grade, percent_grade, verified):
    GRADE_CHANGE_EVENT_PRODUCER.produce("credentials_grade_change", key=str(uuid4()),
                                        value=GradeChangeEvent(
                                            username=getattr(user, 'username', None),
                                            course_run=str(course_run_key),
                                            letter_grade=letter_grade,
                                            percent_grade=percent_grade,
                                            verified=verified
                                        ))
    GRADE_CHANGE_EVENT_PRODUCER.poll()

