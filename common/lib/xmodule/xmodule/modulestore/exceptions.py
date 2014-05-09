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

    def __str__(self, *args, **kwargs):
        """
        Print info about what's duplicated
        """
        return '{0.store}[{0.collection}] already has {0.element_id}'.format(
            self, Exception.__str__(self, *args, **kwargs)
        )

class VersionConflictError(Exception):
    """
    The caller asked for either draft or published head and gave a version which conflicted with it.
    """
    def __init__(self, requestedLocation, currentHeadVersionGuid):
        super(VersionConflictError, self).__init__()
        self.requestedLocation = requestedLocation
        self.currentHeadVersionGuid = currentHeadVersionGuid


class DuplicateCourseError(Exception):
    """
    An attempt to create a course whose id duplicates an existing course's
    """
    def __init__(self, course_id, existing_entry):
        """
        existing_entry will have the who, when, and other properties of the existing entry
        """
        super(DuplicateCourseError, self).__init__()
        self.course_id = course_id
        self.existing_entry = existing_entry
