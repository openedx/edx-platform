class InvalidDefinitionError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ProcessingError(Exception):
    '''
    An error occurred while processing a request to the XModule.
    For example: if an exception occurs while checking a capa problem.
    '''
    pass

class InvalidVersionError(Exception):
    """
    Tried to save an item with a location that a store cannot support (e.g., draft version
    for a non-leaf node)
    """
    def __init__(self, location):
        super(InvalidVersionError, self).__init__()
        self.location = location
