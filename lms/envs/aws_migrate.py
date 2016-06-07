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


def get_db_overrides(db_name):
    """
    Now that we have multiple databases, we want to look up from the environment
    for both databases.
    """
    db_overrides = dict(
        PASSWORD=os.environ.get('DB_MIGRATION_PASS', None),
        ENGINE=os.environ.get('DB_MIGRATION_ENGINE', DATABASES[db_name]['ENGINE']),
        USER=os.environ.get('DB_MIGRATION_USER', DATABASES[db_name]['USER']),
        NAME=os.environ.get('DB_MIGRATION_NAME', DATABASES[db_name]['NAME']),
        HOST=os.environ.get('DB_MIGRATION_HOST', DATABASES[db_name]['HOST']),
        PORT=os.environ.get('DB_MIGRATION_PORT', DATABASES[db_name]['PORT']),
    )

    if db_overrides['PASSWORD'] is None:
        raise ImproperlyConfigured("No database password was provided for running "
                                   "migrations.  This is fatal.")
    return db_overrides

for db in DATABASES:
    # You never migrate a read_replica
    if db != 'read_replica':
        DATABASES[db].update(get_db_overrides(db))
