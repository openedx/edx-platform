"""API base classes in support of the individual User API endpoint implementations.
"""


class UserApiRequestError(Exception):
    """There was a problem with the request to the User API. """
    pass


class UserApiInternalError(Exception):
    """An internal error occurred in the User API. """
    pass


class UserNotFound(UserApiRequestError):
    """The requested user does not exist. """
    pass


class UserNotAuthorized(UserApiRequestError):
    """The user is not authorized to perform the requested action. """
    pass
