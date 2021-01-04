"""
Exceptions related to the handling of profile images.
"""


from six import text_type


class ImageValidationError(Exception):
    """
    Exception to use when the system rejects a user-supplied source image.
    """
    @property
    def user_message(self):
        """
        Translate the developer-facing exception message for API clients.
        """
        return text_type(self)
