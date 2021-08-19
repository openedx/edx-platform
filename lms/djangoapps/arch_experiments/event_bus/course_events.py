from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka import SerializingProducer
from django.conf import settings


course_event_key_schema = """
    {
        "namespace": "djangoapps.arch_experiments.event_bus",
        "name": "CourseEventKey",
        "type": "record",
        "fields": [
            {"name": "course_key", "type": "string"}
        ]
    }
"""

class CourseEventKey:
    def __init__(self, key):
        self.course_key = key

    @staticmethod
    def from_dict(obj, ctx):
        return CourseEventKey(obj['course_key'])

    @staticmethod
    def to_dict(course_event_key, ctx):
        return { "course_key": course_event_key.course_key }

course_schema = """
    {
        "namespace":"djangoapps.arch_experiments.event_bus",
        "name": "Course",
        "type": "record",
        "fields": [
            {"name":"course_key", "type":"string"},
            {"name":"title", "type":"string"},
            {"name":"organization","type":"string"}
        ]
    }
"""

course_event_value_schema = """
    {
        "namespace": "djangoapps.arch_experiments.event_bus",
        "name": "CourseEnrollmentEventValue",
        "type": "record",
        "fields": [
            {
                "name":"course", 
                "type": {
                    "type":"record",
                    "name":"Course",
                    "fields": [
                        {"name":"course_key", "type":"string"},
                        {"name":"title", "type":"string"},
                        {"name":"organization","type":"string"}
                    ]
                }
            },
            {"name": "user_id", "type": "string"},
            {"name": "is_enroll", "type": "boolean"}
        ]
    }
"""

class Course:
    def __init__(self, course_key, title, org):
        self.course_key = course_key
        self.title = title
        self.organization = org

    def formatted_title(self):
        return f"{self.title} from {self.organization}"

class CourseEnrollmentEventValue:
    def __init__(self, course, user_id, is_enroll):
        self.course = course
        self.user_id = user_id
        self.is_enroll = is_enroll

    @staticmethod
    def from_dict(obj, ctx):
        return CourseEnrollmentEventValue(
            Course(obj['course']['course_key'], obj['course']['title'], obj['course']['organization']),
            obj['user_id'],
            obj['is_enroll']
        )

    @staticmethod
    def to_dict(course_enrollment, ctx):
        return {
            "course": {
                "title": course_enrollment.course.title,
                "course_key": course_enrollment.course.course_key,
                "organization": course_enrollment.course.organization,
            },
            "user_id": course_enrollment.user_id,
            "is_enroll": course_enrollment.is_enroll,
        }


SCHEMA_REGISTRY_CLIENT = SchemaRegistryClient({
    'url': settings.SCHEMA_REGISTRY_URL,
})
COURSE_EVENT_KEY_SERIALIZER = AvroSerializer(schema_str=course_event_key_schema, schema_registry_client=SCHEMA_REGISTRY_CLIENT,
                                             to_dict = CourseEventKey.to_dict)
COURSE_EVENT_VALUE_SERIALIZER = AvroSerializer(schema_str=course_event_value_schema, schema_registry_client= SCHEMA_REGISTRY_CLIENT,
                                             to_dict = CourseEnrollmentEventValue.to_dict)
COURSE_EVENT_KEY_DESERIALIZER = AvroDeserializer(schema_str=course_event_key_schema, schema_registry_client=SCHEMA_REGISTRY_CLIENT,
                                                 from_dict= CourseEventKey.from_dict)
COURSE_EVENT_VALUE_DESERIALIZER = AvroDeserializer(schema_str=course_event_value_schema, schema_registry_client=SCHEMA_REGISTRY_CLIENT,
                                                   from_dict = CourseEnrollmentEventValue.from_dict)
