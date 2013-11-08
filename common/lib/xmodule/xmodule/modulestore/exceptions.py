"""
Exceptions thrown by KeyStore objects
"""


class ItemNotFoundError(Exception):
    pass


class ItemWriteConflictError(Exception):
    pass


class InsufficientSpecificationError(Exception):
    pass


class OverSpecificationError(Exception):
    pass


class InvalidLocationError(Exception):
    pass


class NoPathToItem(Exception):
    pass


class DuplicateItemError(Exception):
    """
    Attempted to create an item which already exists.
    """
    def __init__(self, element_id, store=None, collection=None):
        super(DuplicateItemError, self).__init__()
        self.element_id = element_id
        self.store = store
        self.collection = collection


class VersionConflictError(Exception):
    """
    The caller asked for either draft or published head and gave a version which conflicted with it.
    """
    def __init__(self, requestedLocation, currentHeadVersionGuid):
        super(VersionConflictError, self).__init__()
        self.requestedLocation = requestedLocation
        self.currentHeadVersionGuid = currentHeadVersionGuid
