"""
This config file follows the devstack enviroment, but adds the
requirement of a celery worker running in the background to process
celery tasks.

When testing locally, run lms/cms with this settings file as well, to test queueing
of tasks onto the appropriate workers.

In two separate processes on devstack:
    paver devstack lms --settings=devstack_with_worker
    DJANGO_SETTINGS_MODULE=lms.envs.devstack_with_worker celery worker --app=lms.celery:APP
"""


# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import
from lms.envs.devstack import *

# Require a separate celery worker
CELERY_ALWAYS_EAGER = False
CLEAR_REQUEST_CACHE_ON_TASK_COMPLETION = True
BROKER_URL = 'redis://:password@edx.devstack.redis:6379/'
