"""
Exception classes used in lms/courseware.
"""


class Redirect(Exception):
    """
    Exception class that requires redirecting to a URL.
    """
    def __init__(self, url):
        super().__init__()
        self.url = url


class CourseAccessRedirect(Redirect):
    """
    Redirect raised when user does not have access to a course.

    Arguments:
        url (string): The redirect url.
        access_error (AccessErro): The AccessError that caused the redirect.
            The AccessError contains messages for developers and users explaining why
            the user was denied access. These strings can then be exposed to the user.
    """
    def __init__(self, url, access_error=None):
        super().__init__(url)
        self.access_error = access_error


class CourseRunNotFound(ValueError):
    """
    Indicate that a supplied course run key does not map to a course run in the system.
    """

    def __init__(self, course_key):
        """
        Initialize CourseRunNotFound exception.

        Arguments:
            course_key (CourseKey|str):
                course run key or stringified version thereof.
        """
        super().__init__(f"Course run not found: {course_key}")
