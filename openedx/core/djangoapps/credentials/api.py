"""
Python APIs exposed by the credentials app to other in-process apps.
"""


from openedx.core.djangoapps.credentials.models import CredentialsApiConfig


def is_credentials_enabled():
    """
    A utility function wrapping the `is_learner_issurance_enabled` utility function of the CredentialsApiConfig model.
    Intended to be an easier to read/grok utility function that informs the caller if use of the Credentials IDA is
    enabled for this Open edX instance.
    """
    return CredentialsApiConfig.current().is_learner_issuance_enabled
