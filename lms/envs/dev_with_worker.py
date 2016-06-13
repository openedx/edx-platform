"""
This config file follows the dev enviroment, but adds the
requirement of a celery worker running in the background to process
celery tasks.

When testing locally, run lms/cms with this settings file as well, to test queueing
of tasks onto the appropriate workers.

In two separate processes on devstack:
    paver devstack lms --settings=dev_with_worker
    ./manage.py lms celery worker --settings=dev_with_worker
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from lms.envs.dev import *
from os import environ

# SERVICE_VARIANT specifies name of the variant used, which decides what JSON
# configuration files are read during startup.
SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)

# CONFIG_PREFIX specifies the prefix of the JSON configuration files,
# based on the service variant. If no variant is use, don't use a
# prefix.
CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""

################################# CELERY ######################################

# Require a separate celery worker
CELERY_ALWAYS_EAGER = False

# Set up separate lms/cms queues, as done on aws
# Each has slightly different settings, it's important to know which tasks go on which queue
QUEUE_VARIANT = CONFIG_PREFIX.lower()
CELERY_DEFAULT_EXCHANGE = 'edx.{0}core'.format(QUEUE_VARIANT)
HIGH_PRIORITY_QUEUE = 'edx.{0}core.high'.format(QUEUE_VARIANT)
DEFAULT_PRIORITY_QUEUE = 'edx.{0}core.default'.format(QUEUE_VARIANT)
LOW_PRIORITY_QUEUE = 'edx.{0}core.low'.format(QUEUE_VARIANT)
HIGH_MEM_QUEUE = 'edx.{0}core.high_mem'.format(QUEUE_VARIANT)
CELERY_DEFAULT_QUEUE = DEFAULT_PRIORITY_QUEUE
CELERY_DEFAULT_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE
CELERY_QUEUES = {
    HIGH_PRIORITY_QUEUE: {},
    LOW_PRIORITY_QUEUE: {},
    DEFAULT_PRIORITY_QUEUE: {},
    HIGH_MEM_QUEUE: {},
}

# Alternate queues, for when you really need to queue something on a cross-process worker
ALTERNATE_QUEUE_ENVS = environ.get('ALTERNATE_WORKER_QUEUES', '').split()
ALTERNATE_QUEUES = [
    DEFAULT_PRIORITY_QUEUE.replace(QUEUE_VARIANT, alternate + '.')
    for alternate in ALTERNATE_QUEUE_ENVS
]
CELERY_QUEUES.update(
    {
        alternate: {}
        for alternate in ALTERNATE_QUEUES
        if alternate not in CELERY_QUEUES.keys()
    }
)
CELERY_ROUTES = "{}celery.Router".format(QUEUE_VARIANT)

# Celery needs to know about how rabbit is set up
BROKER_URL = "amqp://celery:celery@localhost:5672"
CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'

# Disable transaction management because we are using a worker. Views
# that request a task and wait for the result will deadlock otherwise.
for database_name in DATABASES:
    DATABASES[database_name]['ATOMIC_REQUESTS'] = False
