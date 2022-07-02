Managing Kafka Consumers
--------------

Status
======

In Progress

Context
=======
As outlined in the upcoming OEP-52, edX.org has elected to go with Apache Kafka as our event bus implementation. Though the decision presented here is predicated on this particular edX.org decision, it is included to help other Open edX users evaluate Kafka for their own purposes. The standard pattern for consuming events with Kafka is to poll in a loop and process messages as they come in. According to the Confluent team it is a best practice to limit each consumer to a single topic (Confluent is a platform for industry-scale Kafka management)::
    
    consumer.subscribe(["topic"])
    while True:
        message = consumer.poll()
        ## process message

This ``while True`` loop means whatever is running this consumer will run infinitely and block whatever thread runs it from doing anything else. Thus, this code cannot be run as part of the regular Django web server. It also would not fit neatly onto a celery task, which would put it in direct competition for workers with all other celery tasks and be difficult to scale as the number of topics increases.

Decision
========
edX.org will use Kubernetes to manage containers whose sole purpose is to run a management command, which in turn will run a polling loop against the specified topic. This will enable standard horizontal scaling of Kafka consumer groups.

Rejected Alternatives
=====================
    
#. Create a new ASG of EC2 instances dedicated to running a consumer management command, similar to how we create instances dedicated to running celery workers
    * edX and the industry in general we are moving away from the ASG pattern and on to Kubernetes. Both the ASG approach and the Kubernetes approach would require a substantial amount of work in order to make the number of instances scalable based on number of topics rather than built-in measurements like CPU load. Based on this, it makes more sense to put in the effort in Kubernetes rather than creating more outdated infrastructure.
#. Django-channels
    * Research turned up the possibility of using django-channels (websocket equivalent for Django) for use with Kafka, but the design and potential benefit was unclear so this was not pursued further
