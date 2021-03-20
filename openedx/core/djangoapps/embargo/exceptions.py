"""Exceptions for the embargo app."""


class InvalidAccessPoint(Exception):
    """The requested access point is not supported. """

    def __init__(self, access_point, *args, **kwargs):
        msg = (
            "Access point '{access_point}' should be either 'enrollment' or 'courseware'"
        ).format(access_point=access_point)
<<<<<<< HEAD
        super(InvalidAccessPoint, self).__init__(msg, *args, **kwargs)  # lint-amnesty, pylint: disable=super-with-arguments
=======
        super().__init__(msg, *args, **kwargs)
>>>>>>> 5d7cd3d278cf9ff593e20b4eebd5aad1249d3308
