"""
Errors thrown by the various user APIs.
"""


class UserAPIRequestError(Exception):
    """There was a problem with the request to the User API. """
    pass


class UserAPIInternalError(Exception):
    """An internal error occurred in the User API. """
    pass


class UserNotFound(UserAPIRequestError):
    """The requested user does not exist. """
    pass


class UserNotAuthorized(UserAPIRequestError):
    """The user is not authorized to perform the requested action. """
    pass


class AccountRequestError(UserAPIRequestError):
    """There was a problem with the request to the account API. """
    pass


class AccountUserAlreadyExists(AccountRequestError):
    """User with the same username and/or email already exists. """
    pass


class AccountUsernameInvalid(AccountRequestError):
    """The requested username is not in a valid format. """
    pass


class AccountEmailInvalid(AccountRequestError):
    """The requested email is not in a valid format. """
    pass


class AccountPasswordInvalid(AccountRequestError):
    """The requested password is not in a valid format. """
    pass


class AccountUpdateError(AccountRequestError):
    """
    An update to the account failed. More detailed information is present in developer_message,
    and depending on the type of error encountered, there may also be a non-null user_message field.
    """
    def __init__(self, developer_message, user_message=None):
        self.developer_message = developer_message
        self.user_message = user_message


class AccountValidationError(AccountRequestError):
    """
    Validation issues were found with the supplied data. More detailed information is present in field_errors,
    a dict with specific information about each field that failed validation. For each field,
    there will be at least a developer_message describing the validation issue, and possibly
    also a user_message.
    """
    def __init__(self, field_errors):
        self.field_errors = field_errors


class PreferenceRequestError(UserAPIRequestError):
    """There was a problem with a preference request."""
    pass


class PreferenceValidationError(PreferenceRequestError):
    """
    Validation issues were found with the supplied data. More detailed information is present
    in preference_errors, a dict with specific information about each preference that failed
    validation. For each preference, there will be at least a developer_message describing
    the validation issue, and possibly also a user_message.
    """
    def __init__(self, preference_errors):
        self.preference_errors = preference_errors


class PreferenceUpdateError(PreferenceRequestError):
    """
    An update to a user preference failed. More detailed information is present in developer_message,
    and depending on the type of error encountered, there may also be a non-null user_message field.
    """
    def __init__(self, developer_message, user_message=None):
        self.developer_message = developer_message
        self.user_message = user_message


class CountryCodeError(ValueError):
    """There was a problem with the country code"""
    pass
