"""
Celery needs to be loaded when the cms modules are so that task
registration and discovery can work correctly.

Import sorting is intentionally disabled in this module.
isort:skip_file
"""

# FAL-2248: Monkey patch django's get_storage_engine to work around long migrations times.
# This fixes a performance issue with database migrations in Ocim. We will need to keep
# this patch in our opencraft-release/* branches until edx-platform upgrades to Django 4.*
# which will include this commit:
# https://github.com/django/django/commit/518ce7a51f994fc0585d31c4553e2072bf816f76
import django.db.backends.mysql.introspection

# We monkey patch Kombu's entrypoints listing because scanning through this
# accounts for the majority of LMS/Studio startup time for tests, and we don't
# use custom Kombu serializers (which is what this is for). Still, this is
# pretty evil, and should be taken out when we update Celery to the next version
# where it looks like this method of custom serialization has been removed.
#
# FWIW, this is identical behavior to what happens in Kombu if pkg_resources
# isn't available.
import kombu.utils
kombu.utils.entrypoints = lambda namespace: iter([])

# This will make sure the app is always imported when Django starts so
# that shared_task will use this app, and also ensures that the celery
# singleton is always configured for the CMS.
from .celery import APP as CELERY_APP  # lint-amnesty, pylint: disable=wrong-import-position


def get_storage_engine(self, cursor, table_name):
    """
    This is a patched version of `get_storage_engine` that fixes a
    performance issue with migrations. For more info see FAL-2248 and
    https://github.com/django/django/pull/14766
    """
    cursor.execute("""
        SELECT engine
        FROM information_schema.tables
        WHERE table_name = %s
            AND table_schema = DATABASE()""", [table_name])
    result = cursor.fetchone()
    if not result:
        return self.connection.features._mysql_storage_engine  # pylint: disable=protected-access
    return result[0]


django.db.backends.mysql.introspection.DatabaseIntrospection.get_storage_engine = get_storage_engine
