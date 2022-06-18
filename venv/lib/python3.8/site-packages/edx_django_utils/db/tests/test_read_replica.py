"""
Tests of edx_django_utils.db.read_replica.
"""

from importlib import reload

from django.conf import settings
from django.contrib import auth
from django.test import TestCase, override_settings

from .. import read_replica

WRITER_ONLY_DATABASES = settings.DATABASES.copy()
del WRITER_ONLY_DATABASES["read_replica"]

READ_REPLICA_DATABASES = settings.DATABASES
DATABASE_ROUTERS = settings.DATABASE_ROUTERS + [
    "edx_django_utils.db.read_replica.ReadReplicaRouter"
]
User = auth.get_user_model()


class TestReadReplica(TestCase):
    """
    Tests of edx_django_utils.db.read_replica.
    """

    databases = ["default", "read_replica"]

    def setUp(self):
        super().setUp()
        self.addCleanup(reload, read_replica)

    def test_read_inside_write_error(self):
        with self.assertRaises(AssertionError):
            with read_replica.write_queries():
                with read_replica.read_queries_only():
                    pass  # pragma: no cover

    def test_write_inside_read_error(self):
        with self.assertRaises(AssertionError):
            with read_replica.read_queries_only():
                with read_replica.write_queries():
                    pass  # pragma: no cover

    def test_write_inside_write_ok(self):
        with read_replica.write_queries():
            with read_replica.write_queries():
                pass

    def test_read_inside_read_ok(self):
        with read_replica.read_queries_only():
            with read_replica.read_queries_only():
                pass

    def test_read_replica_name_from_default(self):
        reload(read_replica)
        assert read_replica.READ_REPLICA_NAME == "read_replica"

    @override_settings(EDX_READ_REPLICA_DB_NAME="new_read_replica")
    def test_read_replica_name_from_settings(self):
        reload(read_replica)
        assert read_replica.READ_REPLICA_NAME == "new_read_replica"

    @override_settings(DATABASES=WRITER_ONLY_DATABASES)
    def test_writer_name_from_default(self):
        reload(read_replica)
        assert read_replica.WRITER_NAME == "default"

    @override_settings(EDX_WRITER_DB_NAME="new_default")
    def test_writer_name_from_settings(self):
        reload(read_replica)
        assert read_replica.WRITER_NAME == "new_default"

    @override_settings(DATABASES=WRITER_ONLY_DATABASES)
    def test_read_replica_fallback(self):
        reload(read_replica)
        assert read_replica.READ_REPLICA_OR_DEFAULT == read_replica.WRITER_NAME

    @override_settings(DATABASES=READ_REPLICA_DATABASES)
    def test_read_replica_exists(self):
        reload(read_replica)
        assert read_replica.READ_REPLICA_OR_DEFAULT == read_replica.READ_REPLICA_NAME

    @override_settings(
        DATABASES=READ_REPLICA_DATABASES, DATABASE_ROUTERS=DATABASE_ROUTERS
    )
    def test_read_only_queries_from_database(self):
        reload(read_replica)
        User(username="test_user").save(using=read_replica.WRITER_NAME)

        assert User.objects.all().count() == 1
        with read_replica.read_queries_only():
            assert User.objects.all().count() == 0

    @override_settings(
        DATABASES=READ_REPLICA_DATABASES, DATABASE_ROUTERS=DATABASE_ROUTERS
    )
    def test_router_writes(self):
        reload(read_replica)
        User(username="test_user").save()

        assert User.objects.all().count() == 1
        with read_replica.read_queries_only():
            assert User.objects.all().count() == 0
