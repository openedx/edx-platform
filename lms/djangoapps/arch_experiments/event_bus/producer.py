from confluent_kafka import SerializingProducer
from django.conf import settings


# Create only one producer per event type, which is the confluent recommendation
class ProducerFactory:
    _type_to_producer = {}

    @classmethod
    def get_or_create_event_producer(cls, event_type, event_key_serializer, event_value_serializer):
        existing_producer = cls._type_to_producer.get(event_type)
        if existing_producer is not None:
            return existing_producer
        producer_settings = dict(settings.KAFKA_PRODUCER_CONF_BASE)
        producer_settings.update({'key.serializer': event_key_serializer,
                                  'value.serializer': event_value_serializer})
        new_producer = SerializingProducer(producer_settings)
        cls._type_to_producer[event_type] = new_producer
        return new_producer
