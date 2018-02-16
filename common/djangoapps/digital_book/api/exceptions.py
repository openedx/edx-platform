""""
Exception classes used in digital_book
"""
from lms.djangoapps.courseware.exceptions import Redirect

class DigitalBookAccessRedirect(Redirect):
    """
    Redirect raised when user does not have access to a digital book

    Arguments:
        url (string): The redirect url.
        access_error (AccessError): The AccessError that caused the redirect.
    """
    def __init__(self, url, access_error=None):
        super(DigitalBookAccessRedirect, self).__init__(url)
        self.access_error = access_error


