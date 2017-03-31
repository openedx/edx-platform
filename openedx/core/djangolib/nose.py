"""
Utilities related to nose.
"""
from __future__ import absolute_import

from django.core.management import call_command
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections, transaction
from django_nose.plugin import DjangoSetUpPlugin, ResultPlugin, TestReorderer
import django_nose
import django_nose.runner
import nose.core


class NoseTestSuiteRunner(django_nose.NoseTestSuiteRunner):
    """Custom NoseTestSuiteRunner."""

    def setup_databases(self):
        """ Setup databases and then flush to remove data added by migrations. """

        import django.core.management
        real_call_command = django.core.management.call_command

        def suppress_loaddata_call_command(name, *args, **kwargs):
            if name == 'loaddata':
                return 0
            else:
                print name
                return real_call_command(name, *args, **kwargs)

        django.core.management.call_command = suppress_loaddata_call_command
        return_value = super(NoseTestSuiteRunner, self).setup_databases()
        django.core.management.call_command = real_call_command

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

    def run_suite(self, nose_argv):
        """
        Run the suite, but be smarter about invoking django.setup() again.

        This is almost identical to the superclass implementation, except that
        we don't run django.setup() if settings are already configured, to save
        on startup times.
        """
        result_plugin = ResultPlugin()
        plugins_to_add = [
            DjangoSetUpPlugin(self),
            result_plugin,
            TestReorderer()
        ]

        for plugin in django_nose.runner._get_plugins_from_settings():
            plugins_to_add.append(plugin)

        if not settings.configured:
            django.setup()

        nose.core.TestProgram(
            argv=nose_argv, exit=False, addplugins=plugins_to_add
        )

        return result_plugin.result