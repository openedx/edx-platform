class PaymentException(Exception):
    pass

class CCProcessorException(PaymentException):
    pass

class CCProcessorDataException(CCProcessorException):
    pass

class CCProcessorWrongAmountException(CCProcessorException):
    pass