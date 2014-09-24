"""
Utility functions related to databases.
"""
from functools import wraps

from django.db import connection, transaction


def commit_on_success_with_read_committed(func):  # pylint: disable=invalid-name
    """
    Decorator which executes the decorated function inside a transaction with isolation level set to READ COMMITTED.

    If the function returns a response the transaction is committed and if the function raises an exception the
    transaction is rolled back.

    Note: This only works on MySQL.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):  # pylint: disable=missing-docstring

        if connection.vendor == 'mysql':
            # The isolation level cannot be changed while a transaction is in progress. So we close any existing one.
            if connection.transaction_state:
                connection.commit()

            # This will set the transaction isolation level to READ COMMITTED for the next transaction.
            cursor = connection.cursor()
            cursor.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")

        with transaction.commit_on_success():
            return func(*args, **kwargs)

    return wrapper
