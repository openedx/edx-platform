"""Exceptions raised by the credit API. """


class CreditApiBadRequest(Exception):
    """
    Could not complete a request to the credit API because
    there was a problem with the request (as opposed to an internal error).
    """
    pass


class InvalidCreditRequirements(CreditApiBadRequest):
    """
    The requirement dictionary provided has invalid format.
    """
    pass


class InvalidCreditCourse(CreditApiBadRequest):
    """
    The course is not configured for credit.
    """
    pass


class UserIsNotEligible(CreditApiBadRequest):
    """
    The user has not satisfied eligibility requirements for credit.
    """
    pass


class CreditProviderNotConfigured(CreditApiBadRequest):
    """
    The requested credit provider is not configured correctly for the course.
    """
    pass


class RequestAlreadyCompleted(CreditApiBadRequest):
    """
    The user has already submitted a request and received a response from the credit provider.
    """
    pass


class CreditRequestNotFound(CreditApiBadRequest):
    """
    The request does not exist.
    """
    pass


class InvalidCreditStatus(CreditApiBadRequest):
    """
    The status is not either "approved" or "rejected".
    """
    pass
