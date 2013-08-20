class PaymentException(Exception):
    pass

class PurchasedCallbackException(PaymentException):
    pass