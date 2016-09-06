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
