"""
General class for test migrations.Based off an implementation provided at
https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
"""
# pylint: disable=redefined-outer-name

from django.db.migrations.recorder import MigrationRecorder
from django.test import TransactionTestCase
from django.core.management import call_command


class TestMigrations(TransactionTestCase):
    """ Base class for testing migrations. """
    migrate_from = None
    migrate_to = None
    app = None

    @classmethod
    def setUpClass(cls):
        """ Record most_recent_migration and data checking before tests start. """
        super(TestMigrations, cls).setUpClass()
        assert cls.migrate_from and cls.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_from properties".format(type(cls).__name__)
        assert cls.app, "app must be define in the TestCase"
        cls.most_recent_migration = MigrationRecorder.Migration.objects.filter(app=cls.app).last().name

    @classmethod
    def tearDownClass(cls):
        """ Back to most_recent_migration after excecuting all tests. """
        super(TestMigrations, cls).tearDownClass()
        call_command("migrate", cls.app, cls.most_recent_migration)
        cls._check_migration_state(cls.app, cls.most_recent_migration)

    @classmethod
    def _check_migration_state(cls, app, migration_name):
        """ Veirfy the migration from djano migration table. """
        migration_state = MigrationRecorder.Migration.objects.filter(app=app).last()
        assert (migration_state.name == migration_name), "Migrate to %s failed." % migration_name

    def execute_migration(self, migrate_from, migrate_to):
        """
        Execute migration from state to another.
        """
        # Reverse to the original migration
        call_command("migrate", self.app, migrate_from)

        self.setUpBeforeMigration()

        # Run the migration to test
        call_command("migrate", self.app, migrate_to)

    def setUpBeforeMigration(self):  # pylint: disable=invalid-name
        """
        Will run before migration using config field migrate_from.
        Implemented in derived class.
        """
        pass

    def migrate_forwards(self):
        """ Execute migration to forward state. """
        self.execute_migration(self.migrate_from, self.migrate_to)
        TestMigrations._check_migration_state(self.app, self.migrate_to)

    def migrate_backwards(self):
        """ Execute migration to backward state. """
        call_command("migrate", self.app, self.migrate_from)
        TestMigrations._check_migration_state(self.app, self.migrate_from)
