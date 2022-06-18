""" Custom exceptions. """


class UserInfoRetrievalFailed(Exception):
    """ Raised when we fail to retrieve user info (e.g. from the OAuth provider). """
