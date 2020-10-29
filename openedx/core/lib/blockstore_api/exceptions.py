"""
Exceptions that may be raised by the Blockstore API
"""
from __future__ import absolute_import, division, print_function, unicode_literals


class BlockstoreException(Exception):
    pass


class NotFound(BlockstoreException):
    pass


class CollectionNotFound(NotFound):
    pass


class BundleNotFound(NotFound):
    pass


class DraftNotFound(NotFound):
    pass


class BundleFileNotFound(NotFound):
    pass
