"""
Exceptions are handling in separate file.
"""
# pylint: disable=missing-docstring


#Exceptions for the certificate app
class CertificateException(Exception):
    pass


class CertificateValidationError(CertificateException):
    """
    An exception raised when certificate information is invalid.
    """
    pass
