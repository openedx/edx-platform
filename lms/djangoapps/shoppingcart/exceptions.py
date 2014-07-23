"""
Exceptions for the shoppingcart app
"""
# (Exception Class Names are sort of self-explanatory, so skipping docstring requirement)
# pylint: disable=C0111

class PaymentException(Exception):
    pass


class PurchasedCallbackException(PaymentException):
    pass


class InvalidCartItem(PaymentException):
    pass


class ItemAlreadyInCartException(InvalidCartItem):
    pass


class AlreadyEnrolledInCourseException(InvalidCartItem):
    pass


class CourseDoesNotExistException(InvalidCartItem):
    pass


class CouponDoesNotExistException(InvalidCartItem):
    pass


class CouponAlreadyExistException(InvalidCartItem):
    pass


class ItemDoesNotExistAgainstCouponException(InvalidCartItem):
    pass


class RegCodeAlreadyExistException(InvalidCartItem):
    pass


class ItemDoesNotExistAgainstRegCodeException(InvalidCartItem):
    pass


class ReportException(Exception):
    pass


class ReportTypeDoesNotExistException(ReportException):
    pass
