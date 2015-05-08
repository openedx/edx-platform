"""
A common module for managing exceptions. Helps to avoid circular references
"""


# Certificates Exceptions
class CertificateException(Exception):
    """
    Base exception for Certificates workflows
    """
    pass


class CertificateValidationError(CertificateException):
    """
    An exception raised when certificate information is invalid.
    """
    pass


class AssetNotFoundException(Exception):
    """
    Raised when asset not found
    """
    pass
