"""
Utility functions related to databases.
"""
# TransactionManagementError used below actually *does* derive from the standard "Exception" class.
# pylint: disable=nonstandard-exception
from functools import wraps
import random

from django.db import DEFAULT_DB_ALIAS, DatabaseError, Error, transaction


MYSQL_MAX_INT = (2 ** 31) - 1


class CommitOnSuccessManager(object):
    """
    This class implements the commit_on_success() API that was available till Django 1.5.

    An instance can be used either as a decorator or as a context manager. However, it
    cannot be nested inside an atomic block.

    It is mostly taken from https://github.com/django/django/blob/1.8.5/django/db/transaction.py#L110-L277
    but instead of using save points commits all pending queries at the end of a block.

    The goal is to behave as close as possible to:
    https://github.com/django/django/blob/1.4.22/django/db/transaction.py#L263-L289
    """

    # Tests in TestCase subclasses are wrapped in an atomic block to speed up database restoration.
    # So we must disabled this manager.
    # https://github.com/django/django/blob/1.8.5/django/core/handlers/base.py#L129-L132
    ENABLED = True

    def __init__(self, using, read_committed=False):
        self.using = using
        self.read_committed = read_committed

    def __enter__(self):

        if not self.ENABLED:
            return

        connection = transaction.get_connection(self.using)

        if connection.in_atomic_block:
            raise transaction.TransactionManagementError('Cannot be inside an atomic block.')

        if getattr(connection, 'commit_on_success_block_level', 0) == 0:
            connection.commit_on_success_block_level = 1

            # This will set the transaction isolation level to READ COMMITTED for the next transaction.
            if self.read_committed is True:
                if connection.vendor == 'mysql':
                    cursor = connection.cursor()
                    cursor.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")

            # We aren't in a transaction yet; create one.
            # The usual way to start a transaction is to turn autocommit off.
            # However, some database adapters (namely sqlite3) don't handle
            # transactions and savepoints properly when autocommit is off.
            # In such cases, start an explicit transaction instead, which has
            # the side-effect of disabling autocommit.
            if connection.features.autocommits_when_autocommit_is_off:
                connection._start_transaction_under_autocommit()  # pylint: disable=protected-access
                connection.autocommit = False
            else:
                connection.set_autocommit(False)
        else:
            if self.read_committed is True:
                raise transaction.TransactionManagementError('Cannot change isolation level when nested.')

            connection.commit_on_success_block_level += 1

    def __exit__(self, exc_type, exc_value, traceback):

        if not self.ENABLED:
            return

        connection = transaction.get_connection(self.using)

        try:
            if exc_type is None:
                # Commit transaction
                try:
                    connection.commit()
                except DatabaseError:
                    try:
                        connection.rollback()
                    except Error:
                        # An error during rollback means that something
                        # went wrong with the connection. Drop it.
                        connection.close()
                    raise
            else:
                # Roll back transaction
                try:
                    connection.rollback()
                except Error:
                    # An error during rollback means that something
                    # went wrong with the connection. Drop it.
                    connection.close()

        finally:
            connection.commit_on_success_block_level -= 1

            # Outermost block exit when autocommit was enabled.
            if connection.commit_on_success_block_level == 0:
                if connection.features.autocommits_when_autocommit_is_off:
                    connection.autocommit = True
                else:
                    connection.set_autocommit(True)

    def __call__(self, func):
        @wraps(func)
        def decorated(*args, **kwds):       # pylint: disable=missing-docstring
            with self:
                return func(*args, **kwds)
        return decorated


def commit_on_success(using=None, read_committed=False):
    """
    This function implements the commit_on_success() API that was available till Django 1.5.

    It can be used either as a decorator or as a context manager. However, it
    cannot be nested inside an atomic block.

    If the wrapped function or block returns a response the transaction is committed
    and if it raises an exception the transaction is rolled back.

    Arguments:
        using (str): the name of the database.
        read_committed (bool): Whether to use read committed isolation level.

    Raises:
        TransactionManagementError: if already inside an atomic block.
    """
    if callable(using):
        return CommitOnSuccessManager(DEFAULT_DB_ALIAS, read_committed)(using)
    # Decorator: @commit_on_success(...) or context manager: with commit_on_success(...): ...
    else:
        return CommitOnSuccessManager(using, read_committed)


class OuterAtomic(transaction.Atomic):
    """
    Atomic which cannot be nested in another atomic.

    This is useful if you want to ensure that a commit happens at
    the end of the wrapped block.
    """
    ALLOW_NESTED = False

    def __init__(self, using, savepoint, read_committed=False):
        self.read_committed = read_committed
        super(OuterAtomic, self).__init__(using, savepoint)

    def __enter__(self):

        connection = transaction.get_connection(self.using)

        # TestCase setup nests tests in two atomics - one for the test class and one for the individual test.
        # The outermost atomic starts a transaction - so does not have a savepoint.
        # The inner atomic starts a savepoint around the test.
        # So, for tests only, there should be exactly one savepoint_id and two atomic_for_testcase_calls.
        # atomic_for_testcase_calls below is added in a monkey-patch for tests only.
        if self.ALLOW_NESTED and (self.atomic_for_testcase_calls - len(connection.savepoint_ids)) < 1:
            raise transaction.TransactionManagementError('Cannot be inside an atomic block.')

        # Otherwise, this shouldn't be nested in any atomic block.
        if not self.ALLOW_NESTED and connection.in_atomic_block:
            raise transaction.TransactionManagementError('Cannot be inside an atomic block.')

        # This will set the transaction isolation level to READ COMMITTED for the next transaction.
        if self.read_committed is True:
            if connection.vendor == 'mysql':
                cursor = connection.cursor()
                cursor.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")

        super(OuterAtomic, self).__enter__()


def outer_atomic(using=None, savepoint=True, read_committed=False):
    """
    A variant of Django's atomic() which cannot be nested inside another atomic.

    With the upgrade to Django 1.8, all views by default are wrapped
    in an atomic block. Because of this, a commit to the database can
    only happen once the view returns. This is because nested atomic
    blocks use savepoints and the transaction only gets committed when
    the outermost atomic block returns. See the official Django docs
    for details: https://docs.djangoproject.com/en/1.8/topics/db/transactions/

    However, in some cases, we need to be able to commit to the
    database in the middle of a view. The only way to do this
    is to disable automatic transaction management for the view by
    adding @transaction.non_atomic_requests to it and then using
    atomic() inside it in relevant places. To help ensure that queries
    inside a piece of code are committed, you can wrap it in
    outer_atomic(). outer_atomic() will ensure that it is not nested
    inside another atomic block.

    Additionally, some views need to use READ COMMITTED isolation level.
    For this add @transaction.non_atomic_requests and
    @outer_atomic(read_committed=True) decorators on it.

    Arguments:
        using (str): the name of the database.
        read_committed (bool): Whether to use read committed isolation level.

    Raises:
        TransactionManagementError: if already inside an atomic block.
    """
    if callable(using):
        return OuterAtomic(DEFAULT_DB_ALIAS, savepoint, read_committed)(using)
    # Decorator: @outer_atomic(...) or context manager: with outer_atomic(...): ...
    else:
        return OuterAtomic(using, savepoint, read_committed)


def generate_int_id(minimum=0, maximum=MYSQL_MAX_INT, used_ids=None):
    """
    Return a unique integer in the range [minimum, maximum], inclusive.
    """
    if used_ids is None:
        used_ids = []

    cid = random.randint(minimum, maximum)

    while cid in used_ids:
        cid = random.randint(minimum, maximum)

    return cid
