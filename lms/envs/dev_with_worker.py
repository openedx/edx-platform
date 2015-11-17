"""
This config file follows the dev enviroment, but adds the
requirement of a celery worker running in the background to process
celery tasks.

The worker can be executed using:

django_admin.py celery worker
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from lms.envs.dev import *

################################# CELERY ######################################

# Requires a separate celery worker

CELERY_ALWAYS_EAGER = False

# Use django db as the broker and result store

BROKER_URL = 'django://'
INSTALLED_APPS += ('djcelery.transport', )
CELERY_RESULT_BACKEND = 'database'
DJKOMBU_POLLING_INTERVAL = 1.0

# Disable transaction management because we are using a worker. Views
# that request a task and wait for the result will deadlock otherwise.
for database_name in DATABASES:
    DATABASES[database_name]['ATOMIC_REQUESTS'] = False
