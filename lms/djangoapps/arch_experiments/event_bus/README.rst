======================
Event Bus - Experiment
======================
A toy app with just two management commands to demonstrate how to produce
and consume events with Kafka and Avro.

To run:

1. Make sure the Confluent containers are all up and running in devstack (`make dev.up.kafka-rest-proxy` will bring up all of them). This sometimes takes a few minutes. To check if it is up, you can look at localhost:8082/topics in your browser. You can also just bring up kafka, schema-registry, and zookeeper individually (the rest proxy is mostly for debugging).

2. In the lms shell, run ``./manage.py lms produce_test_message``. This will produce messages to ``test-topic`` unless you specify otherwise with ``--topic <mytopic>``

3. In the lms shell, rum ``./manage.py lms consume_test_message``. This will consume messages from ``test-topic`` unless you specify otherwise with ``--topic <mytopic>``

Notes for Development
------------------
- In devstack, we can talk to the kafka container without any authentication. Once the real kafka instance is up and running in confluent, settings.KAFKA_CONSUMER_CONF_BASE and settings.KAFKA_PRODUCER_CONF_BASE will need some extra parameters to handle authentication.

- Though the consumer and producer are only initialized once in the app, because management commands run the app startup code every time, running the management commands will create new consumer/producer instances every time. This means that running two ``consume_test_message`` commands at the same time will add two consumers to the consumer group ``lms``. Only one of them will receive messages at a time (experiments suggest it will always be the most recent one to be started, at least with a low number of messages). This is how Kafka does 'exactly-once' reads. 

- For production-level events, we may need to sort out how to share instances of the producer and consumer. According to the documentation this should be possible and is preferable, at least in the case of the producer. See https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#confluent_kafka.SerializingProducer .
