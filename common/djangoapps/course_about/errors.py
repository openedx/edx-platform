"""
Contains all the errors associated with the Course About API.

"""


class CourseAboutError(Exception):
    """Generic Course About Error"""

    def __init__(self, msg, data=None):
        super(CourseAboutError, self).__init__(msg)
        # Corresponding information to help resolve the error.
        self.data = data


class CourseAboutApiLoadError(CourseAboutError):
    """The data API could not be loaded. """
    pass


class CourseNotFoundError(CourseAboutError):
    """The Course Not Found. """
    pass
