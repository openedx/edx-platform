""" E-Commerce-related exceptions. """


class ApiError(Exception):
    """ Base class for E-Commerce API errors. """
    pass


class InvalidConfigurationError(ApiError):
    """ Exception raised when the API is not properly configured (e.g. settings are not set). """
    pass


class InvalidResponseError(ApiError):
    """ Exception raised when an API response is invalid. """
    pass


class TimeoutError(ApiError):
    """ Exception raised when an API requests times out. """
    pass
