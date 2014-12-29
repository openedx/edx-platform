"""
Exceptions for Payment Processing
"""
# (Exception Class Names are sort of self-explanatory, so skipping docstring requirement)
# pylint: disable=missing-docstring

from shoppingcart.exceptions import PaymentException


class CCProcessorException(PaymentException):
    pass


class CCProcessorSignatureException(CCProcessorException):
    pass


class CCProcessorDataException(CCProcessorException):
    pass


class CCProcessorWrongAmountException(CCProcessorException):
    pass


class CCProcessorUserCancelled(CCProcessorException):
    pass


class CCProcessorUserDeclined(CCProcessorException):
    """Transaction declined."""
    pass


class CCProcessorFailedSyncronization(CCProcessorException):
    pass
