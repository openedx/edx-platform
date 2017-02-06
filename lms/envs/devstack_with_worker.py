"""
This config file follows the devstack enviroment, but adds the
requirement of a celery worker running in the background to process
celery tasks.

When testing locally, run lms/cms with this settings file as well, to test queueing
of tasks onto the appropriate workers.

In two separate processes on devstack:
    paver devstack lms --settings=devstack_with_worker
    ./manage.py lms celery worker --settings=devstack_with_worker
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import
from lms.envs.devstack import *

# Require a separate celery worker
CELERY_ALWAYS_EAGER = False

# Disable transaction management because we are using a worker. Views
# that request a task and wait for the result will deadlock otherwise.
for database_name in DATABASES:
    DATABASES[database_name]['ATOMIC_REQUESTS'] = False
