"""
Exceptions thrown by KeyStore objects
"""


class ItemNotFoundError(Exception):
    pass


class ItemWriteConflictError(Exception):
    pass


class InsufficientSpecificationError(Exception):
    pass


class InvalidLocationError(Exception):
    pass


class NoPathToItem(Exception):
    pass


class DuplicateItemError(Exception):
    pass

class NotDraftVersion(Exception):
    """
    A caller attempted to change a course but was not using the draftVersion.
    """
    def __init__(self, requestedLocation, currentHead):
        super(NotDraftVersion, self).__init__()
        self.requestedLocation = requestedLocation
        self.currentHead = currentHead

class VersionConflictError(Exception):
    """
    The caller asked for either draft or published head and gave a version which conflicted with it.
    """
    def __init__(self, requestedLocation, currentHead):
        super(VersionConflictError, self).__init__()
        self.requestedLocation = requestedLocation
        self.currentHead = currentHead
