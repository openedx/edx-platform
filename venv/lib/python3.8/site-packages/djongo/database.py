from logging import getLogger
from pymongo import MongoClient

logger = getLogger(__name__)
clients = {}


def connect(db, **kwargs):
    try:
        return clients[db]
    except KeyError:
        logger.debug('New MongoClient connection')
        clients[db] = MongoClient(**kwargs, connect=False)
    return clients[db]


class Error(Exception):  # NOQA: StandardError undefined on PY3
    pass


class InterfaceError(Error):
    pass


class DatabaseError(Error):
    pass


class DataError(DatabaseError):
    pass


class OperationalError(DatabaseError):
    pass


class IntegrityError(DatabaseError):
    pass


class InternalError(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    pass


class NotSupportedError(DatabaseError):
    pass


def Binary(value):
    return value
