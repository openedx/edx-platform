#!/usr/bin/env python3

from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka import SerializingProducer
from django.conf import settings

import attr

from opaque_keys.edx.keys import CourseKey

from openedx_events.avro_attrs_bridge import KafkaWrapper
from openedx_events.avro_attrs_bridge_extensions import (
    CourseKeyAvroAttrsBridgeExtension,
    DatetimeAvroAttrsBridgeExtension,
)
from openedx_events.learning.data import (
    CourseEnrollmentData,
    UserData,
    CourseData,
    UserPersonalData,
)

key_bridge = KafkaWrapper(
    CourseData,
    extensions={
        CourseKeyAvroAttrsBridgeExtension.cls: CourseKeyAvroAttrsBridgeExtension(),
        DatetimeAvroAttrsBridgeExtension.cls: DatetimeAvroAttrsBridgeExtension(),
    },
)
key_schema = key_bridge.schema()
value_bridge = KafkaWrapper(
    CourseEnrollmentData,
    extensions={
        CourseKeyAvroAttrsBridgeExtension.cls: CourseKeyAvroAttrsBridgeExtension(),
        DatetimeAvroAttrsBridgeExtension.cls: DatetimeAvroAttrsBridgeExtension(),
    },
)
value_schema = value_bridge.schema()
SCHEMA_REGISTRY_CLIENT = SchemaRegistryClient({
    'url': settings.SCHEMA_REGISTRY_URL,
})

COURSE_EVENT_KEY_SERIALIZER = key_bridge.serialize_wrapper

# AvroSerializer(schema_str=key_schema, schema_registry_client=SCHEMA_REGISTRY_CLIENT,
#                                              to_dict = key_bridge.to_dict)
COURSE_EVENT_VALUE_SERIALIZER = value_bridge.serialize_wrapper

# AvroSerializer(schema_str=value_schema, schema_registry_client= SCHEMA_REGISTRY_CLIENT,
#                                              to_dict = value_bridge.to_dict)
COURSE_EVENT_KEY_DESERIALIZER = key_bridge.deserialize_wrapper

# AvroDeserializer(schema_str=key_schema, schema_registry_client=SCHEMA_REGISTRY_CLIENT,
#                                                  from_dict= key_bridge.dict_to_attrs)
COURSE_EVENT_VALUE_DESERIALIZER = value_bridge.deserialize_wrapper

# AvroDeserializer(schema_str=value_schema, schema_registry_client=SCHEMA_REGISTRY_CLIENT,
#                                                    from_dict = value_bridge.dict_to_attrs)
