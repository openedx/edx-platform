class PaymentException(Exception):
    pass


class PurchasedCallbackException(PaymentException):
    pass


class InvalidCartItem(PaymentException):
    pass
