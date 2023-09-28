"""
Exceptions for SAML Authentication.
"""


from social_core.exceptions import AuthException


class IncorrectConfigurationException(AuthException):
    """
    Error caused due to incorrect configuration.
    """
    def __str__(self):
        return 'There was an error in SAML authentication flow which might be caused by incorrect SAML configuration.'
