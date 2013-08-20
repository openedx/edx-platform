from shoppingcart.exceptions import PaymentException

class CCProcessorException(PaymentException):
    pass

class CCProcessorDataException(CCProcessorException):
    pass

class CCProcessorWrongAmountException(CCProcessorException):
    pass