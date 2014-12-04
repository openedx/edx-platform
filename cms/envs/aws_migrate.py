"""
A Django settings file for use on AWS while running
database migrations, since we don't want to normally run the
LMS with enough privileges to modify the database schema.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

# Import everything from .aws so that our settings are based on those.
from .aws import *
import os
from django.core.exceptions import ImproperlyConfigured

DB_OVERRIDES = dict(
    PASSWORD=os.environ.get('DB_MIGRATION_PASS', None),
    ENGINE=os.environ.get('DB_MIGRATION_ENGINE', DATABASES['default']['ENGINE']),
    USER=os.environ.get('DB_MIGRATION_USER', DATABASES['default']['USER']),
    NAME=os.environ.get('DB_MIGRATION_NAME', DATABASES['default']['NAME']),
    HOST=os.environ.get('DB_MIGRATION_HOST', DATABASES['default']['HOST']),
    PORT=os.environ.get('DB_MIGRATION_PORT', DATABASES['default']['PORT']),
)

if DB_OVERRIDES['PASSWORD'] is None:
    raise ImproperlyConfigured("No database password was provided for running "
                               "migrations.  This is fatal.")

for override, value in DB_OVERRIDES.iteritems():
    DATABASES['default'][override] = value
