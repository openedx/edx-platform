"""
Settings module for running tests during local development
"""
# pylint: disable=wildcard-import
from .test_base import *


def prevent_migrations(db):
    """
    Adapted from gist https://gist.github.com/nealtodd/2869341f38f5b1eeb86d
    This prevents all migrations from being run and causes database tables
    to be created from the model definitions. This significantly speeds up
    test runs.
    """
    import django
    from django.db import connections
    from django.db.migrations.executor import MigrationExecutor
    django.setup()
    migrated_apps = MigrationExecutor(connections[db]).loader.migrated_apps
    return dict(zip(migrated_apps, ['{a}.notmigrations'.format(a=a) for a in migrated_apps]))


MIGRATION_MODULES = prevent_migrations('default')
