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


class SerializationError(Exception):
    """
    Thrown when a module cannot be exported to XML
    """
    def __init__(self, location, msg):
        super(SerializationError, self).__init__(msg)
        self.location = location


class UndefinedContext(Exception):
    """
    Tried to access an xmodule field which needs a different context (runtime) to have a value.
    """
    pass


class HeartbeatFailure(Exception):
    """
    Raised when heartbeat fails.
    """

    def __init__(self, msg, service):
        """
        In addition to a msg, provide the name of the service.
        """
        self.service = service
        super(HeartbeatFailure, self).__init__(msg)
