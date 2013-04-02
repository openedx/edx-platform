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
