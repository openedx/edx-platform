"""
Utilities related to nose.
"""
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections, transaction
import django_nose


class NoseTestSuiteRunner(django_nose.NoseTestSuiteRunner):
    """Custom NoseTestSuiteRunner."""

    def setup_databases(self):
        """ Setup databases and then flush to remove data added by migrations. """
        return_value = super(NoseTestSuiteRunner, self).setup_databases()

        # Delete all data added by data migrations. Unit tests should setup their own data using factories.
        call_command('flush', verbosity=0, interactive=False, load_initial_data=False)

        # Through Django 1.8, auto increment sequences are not reset when calling flush on a SQLite db.
        # So we do it ourselves.
        # http://sqlite.org/autoinc.html
        connection = connections[DEFAULT_DB_ALIAS]
        if connection.vendor == 'sqlite' and not connection.features.supports_sequence_reset:
            with transaction.atomic(using=DEFAULT_DB_ALIAS):
                cursor = connection.cursor()
                cursor.execute(
                    "delete from sqlite_sequence;"
                )

        return return_value
