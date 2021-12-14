from django.conf import settings
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.schema_registry import SchemaRegistryClient

from .events import (
    course_event_value_schema,
    course_event_key_schema,
    CourseEventKey,
    CourseEnrollmentEventValue,
    LicenseTrackingEvent
)

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




LICENSE_EVENT_VALUE_SERIALIZER = AvroSerializer(schema_str=LicenseTrackingEvent.LICENSE_TRACKING_EVENT_AVRO_SCHEMA,
                                                schema_registry_client= SCHEMA_REGISTRY_CLIENT,
                                                to_dict = LicenseTrackingEvent.to_dict)

LICENSE_EVENT_VALUE_DESERIALIZER = AvroDeserializer(schema_str=LicenseTrackingEvent.LICENSE_TRACKING_EVENT_AVRO_SCHEMA,
                                                    schema_registry_client=SCHEMA_REGISTRY_CLIENT,
                                                    from_dict = LicenseTrackingEvent.from_dict)
