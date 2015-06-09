"""Exceptions raised by the credit API. """


class InvalidCreditRequirements(Exception):
    """
    The requirement dictionary provided has invalid format.
    """
    pass


class InvalidCreditCourse(Exception):
    """
    The course is not configured for credit.
    """
    pass


class UserIsNotEligible(Exception):
    """
    The user has not satisfied eligibility requirements for credit.
    """
    pass


class RequestAlreadyCompleted(Exception):
    """
    The user has already submitted a request and received a response from the credit provider.
    """
    pass


class CreditRequestNotFound(Exception):
    """
    The request does not exist.
    """
    pass


class InvalidCreditStatus(Exception):
    """
    The status is not either "approved" or "rejected".
    """
    pass
