"""
A Django settings file for use on AWS while running
database migrations, since we don't want to normally run the
LMS with enough privileges to modify the database schema.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

# Import everything from .aws so that our settings are based on those.
from .aws import *
import os
from django.core.exceptions import ImproperlyConfigured

USER = os.environ.get('DB_MIGRATION_USER', 'root')
PASSWORD = os.environ.get('DB_MIGRATION_PASS', None)

if not PASSWORD:
    raise ImproperlyConfigured("No database password was provided for running "
                               "migrations.  This is fatal.")

DATABASES['default']['USER'] = USER
DATABASES['default']['PASSWORD'] = PASSWORD
