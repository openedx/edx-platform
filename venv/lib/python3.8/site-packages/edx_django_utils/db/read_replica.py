"""
Tools for making queries read from the read-replica database, rather than from the writer database.

The read-replica can be used for
    a. long-running queries that aren't time sensitive
    b. reads of rows that are frequently written, but where reads can be eventually consistent

Settings:
    EDX_READ_REPLICA_DB_NAME: The name of the read-replica in the DATABASES django setting.
        Defaults to "read_replica".
    EDX_WRITER_DB_NAME: The name of the writer in the DATABASES django setting.
        Defaults to "default".
"""
import threading
from contextlib import contextmanager

from django.conf import settings

READ_REPLICA_NAME = getattr(settings, "EDX_READ_REPLICA_DB_NAME", "read_replica")
WRITER_NAME = getattr(settings, "EDX_WRITER_DB_NAME", "default")

READ_REPLICA_OR_DEFAULT = (
    READ_REPLICA_NAME if READ_REPLICA_NAME in settings.DATABASES else WRITER_NAME
)


def use_read_replica_if_available(queryset):
    """
    If there is a database called 'read_replica',
    use that database for the queryset / manager.

    Example usage:
        queryset = use_read_replica_if_available(SomeModel.objects.filter(...))

    Arguments:
        queryset (QuerySet)

    Returns: QuerySet
    """
    return queryset.using(READ_REPLICA_OR_DEFAULT)


def read_replica_or_default():
    """
    If there is a database called READ_REPLICA_DB,
    return READ_REPLICA_DB, otherwise return WRITER_NAME.

    This function is similiar to `use_read_replica_if_available`,
    but is be more syntactically convenient for method call chaining.
    Also, it always falls back to WRITER_NAME,
    no matter what the queryset was using before.

    Example usage:
        queryset = SomeModel.objects.filter(...).using(read_replica_or_default())

    Returns: str
    """
    return READ_REPLICA_OR_DEFAULT


@contextmanager
def read_queries_only():
    """
    A context manager that sets all reads inside it to be from the read-replica.

    It is an error to call this from inside a write_queries context.

    The ReadReplicaRouter must be used for this decorator to affect queries.
    """
    old_db_name = _storage.db_name
    assert (
        old_db_name is None or old_db_name == READ_REPLICA_NAME
    ), "Can't use read_queries_only inside a write_queries contextmanager"
    _storage.db_name = READ_REPLICA_NAME
    try:
        yield
    finally:
        _storage.db_name = old_db_name


@contextmanager
def write_queries():
    """
    A context manager that sets all reads inside it to be from the writer.
    Use this to annotate code that has both reads and writes, where the writes depend
    on the values read. This will allow all of that code to exist within a transaction.

    Using this contextmanager will prevent any contained call from using `read_queries_only`
    in order to read from the read-replica.

    It is an error to call this from inside a read_queries_only context.

    The ReadReplicaRouter must be used for this decorator to affect queries.
    """
    old_db_name = _storage.db_name
    assert (
        old_db_name is None or old_db_name == WRITER_NAME
    ), "Can't use write_queries inside a read_only_queries contextmanager"

    _storage.db_name = WRITER_NAME
    try:
        yield
    finally:
        _storage.db_name = old_db_name


class _ReadReplicaRouterStorage(threading.local):
    def __init__(self):
        super().__init__()
        self.db_name = None


_storage = _ReadReplicaRouterStorage()


class ReadReplicaRouter:
    """
    A database router that by default, reads from the writer database,
    but can be overridden with a context manager to route all reads
    to the read-replica.

    See https://docs.djangoproject.com/en/2.2/topics/db/multi-db/#automatic-database-routing
    """

    def db_for_read(self, model, **hints):  # pylint: disable=unused-argument
        """
        Reads go the active reader name
        """
        return (
            _storage.db_name if _storage.db_name in settings.DATABASES else WRITER_NAME
        )

    def db_for_write(self, model, **hints):  # pylint: disable=unused-argument
        """
        Writes always go to the writer.
        """
        return WRITER_NAME

    def allow_relation(
        self, obj1, obj2, **hints
    ):  # pylint: disable=unused-argument, protected-access
        """
        Relations between objects are allowed if both objects are
        in either the read-replica or the writer.
        """
        db_list = (READ_REPLICA_NAME, WRITER_NAME)
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(
        self, db, app_label, model_name=None, **hints
    ):  # pylint: disable=unused-argument
        """
        All non-auth models end up in this pool.
        """
        return True
