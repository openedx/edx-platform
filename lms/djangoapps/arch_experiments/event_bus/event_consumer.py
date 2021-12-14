from django.conf import settings
from confluent_kafka import KafkaError, KafkaException, Consumer, DeserializingConsumer


consumer_base_settings = dict(settings.KAFKA_CONSUMER_CONF_BASE)


class Consumer:

    def __init__(self, key_deserializer, value_deserializer):
        consumer_settings = dict(consumer_base_settings)
        consumer_settings.update({'key.deserializer': key_deserializer, 'value.deserializer': value_deserializer,
                                  'auto.offset.reset': 'earliest'})
        self._consumer = DeserializingConsumer(consumer_settings)

    def listen(self, topic, callback = None, error_handler = None):
        print("Starting to consume messages...")
        try:
            self._consumer.subscribe([topic])

            while True:
                msg = self._consumer.poll(timeout=1.0)
                if msg is None: continue


                if msg.error():
                    if error_handler is not None:
                        error_handler(msg)
                    elif msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                        print('%% %s [%d] reached end at offset %d\n' %
                          (msg.topic(), msg.partition(), msg.offset()))
                    else:
                        raise KafkaException(msg.error())
                else:
                    callback(msg)
        finally:
        # Close down consumer to commit final offsets.
            self._consumer.close()
