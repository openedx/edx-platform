"""
Exceptions for the shoppingcart app
"""


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


class MultipleCouponsNotAllowedException(InvalidCartItem):
    pass


class RedemptionCodeError(Exception):
    """An error occurs while processing redemption codes. """
    pass


class ReportException(Exception):
    pass


class ReportTypeDoesNotExistException(ReportException):
    pass


class InvalidStatusToRetire(Exception):
    pass


class UnexpectedOrderItemStatus(Exception):
    pass


class ItemNotFoundInCartException(Exception):
    pass
