"""
Specialized exceptions for the SAML SSO and MultiTenantEmails Djangoapp
"""


class SAMLUnusableUsernameDueToMTE(Exception):
    """
    Thrown when a the edge case happens: A user is trying to be automatically
    through a SAML IdP, but the username already exists in a different
    organization. Since this is a weird edge case, we want to raise an
    Exception and deal with the issue manually.
    """
    pass
