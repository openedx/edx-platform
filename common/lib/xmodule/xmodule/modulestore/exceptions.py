"""
Exceptions thrown by KeyStore objects
"""


class ItemNotFoundError(Exception):
    pass


class InsufficientSpecificationError(Exception):
    pass


class InvalidLocationError(Exception):
    pass


class NoPathToItem(Exception):
    pass


class DuplicateItemError(Exception):
    pass
