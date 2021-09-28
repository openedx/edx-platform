Setting Up A Dev Environment for This Code
==========================================

#. Start up pulsar and lms

.. code-block:: shell

    cd /path/to/devstack
    # activate venv
    workon devstack
    make dev.up.pulsar
    make dev.up.lms

#. Enforce schema in pulsar.

.. code-block:: shell

    # In devstack
    make dev.shel.pulsar
    bin/pulsar-admin namespaces set-schema-validation-enforce --enable public/default

#. Run the outbox migration in devstack.

.. code-block:: shell

    make lms-shell
    python manage.py lms migrate arch_experiments

#. Start up the producer.

.. code-block:: shell

    python manage.py lms produce_experiment_topic

#. Start the consumer.

.. code-block:: shell

    python manage.py lms consume_experiment_topic

#. Trigger a message by un-enrolling from a course.
