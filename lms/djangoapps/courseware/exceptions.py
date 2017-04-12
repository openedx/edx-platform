"""
Exception classes used in lms/courseware.
"""


class Redirect(Exception):
    """
    Exception class that requires redirecting to a URL.
    """
    def __init__(self, url):
        super(Redirect, self).__init__()
        self.url = url


class CourseAccessRedirect(Redirect):
    """
    Redirect raised when user does not have access to a course.
    """
    pass
