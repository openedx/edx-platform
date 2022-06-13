"""
Util functions for course live app
"""
from openedx.core.djangoapps.course_live.models import AVAILABLE_PROVIDERS


def provider_requires_pii_sharing(provider_type):
    """
    Check if provider requires any PII ie username or email
    """
    provider = AVAILABLE_PROVIDERS.get(provider_type, None)
    if provider:
        return provider['pii_sharing']['email'] or provider['pii_sharing']['username']
    return False
