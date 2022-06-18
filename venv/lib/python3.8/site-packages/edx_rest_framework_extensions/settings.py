"""
NOTE: Support for multiple JWT_ISSUERS is deprecated.  Instead, Asymmetric JWTs
make this simpler by using JWK keysets to list all available public keys.

Settings for edx-drf-extensions are all namespaced in the EDX_DRF_EXTENSIONS setting.
For example your project's `settings.py` file might look like this:

EDX_DRF_EXTENSIONS = {
    'OAUTH2_ACCESS_TOKEN_URL': 'https://example.com/oauth2/access_token'
}
"""
import logging
import warnings

from django.conf import settings
from rest_framework_jwt.settings import api_settings

from edx_rest_framework_extensions.config import ENABLE_SET_REQUEST_USER_FOR_JWT_COOKIE


logger = logging.getLogger(__name__)


DEFAULT_SETTINGS = {
    'OAUTH2_USER_INFO_URL': None,

    # Map JWT claims to user attributes.
    'JWT_PAYLOAD_USER_ATTRIBUTE_MAPPING': {
        'administrator': 'is_staff',
        'email': 'email',
    },
    'JWT_PAYLOAD_MERGEABLE_USER_ATTRIBUTES': (),
    ENABLE_SET_REQUEST_USER_FOR_JWT_COOKIE: False,
}


def get_setting(name):
    """ Returns the value of the named setting.

        Arguments:
            name (str): Name of the setting to retrieve

        Raises:
            KeyError: The specified setting does not exist.
    """
    try:
        return getattr(settings, 'EDX_DRF_EXTENSIONS', {})[name]
    except KeyError:
        return DEFAULT_SETTINGS[name]


def _get_current_jwt_issuers():
    """
    Internal helper to retrieve the current set of JWT_ISSUERS from the JWT_AUTH configuration
    Having this allows for easier testing/mocking
    """
    # If we have a 'JWT_ISSUERS' list defined, return it
    return settings.JWT_AUTH.get('JWT_ISSUERS', None)


def _get_deprecated_jwt_issuers():
    """
    Internal helper to retrieve the deprecated set of JWT_ISSUER data from the JWT_AUTH configuration
    Having this allows for easier testing/mocking
    """
    # If JWT_ISSUERS is not defined, attempt to return the deprecated settings.
    warnings.warn(
        "'JWT_ISSUERS' list not defined, checking for deprecated settings.",
        DeprecationWarning
    )

    return [
        {
            'ISSUER': api_settings.JWT_ISSUER,
            'SECRET_KEY': api_settings.JWT_SECRET_KEY,
            'AUDIENCE': api_settings.JWT_AUDIENCE
        }
    ]


def get_jwt_issuers():
    """
    Retrieves the JWT_ISSUERS list from system configuraiton.  If no list is defined in JWT_AUTH/JWT_ISSUERS
    an attempt is made to instead return the deprecated JWT configuration settings.
    """
    # If we have a 'JWT_ISSUERS' list defined, return it
    jwt_issuers = _get_current_jwt_issuers()
    if jwt_issuers:
        return jwt_issuers
    # If we do not, return the deprecated configuration
    return _get_deprecated_jwt_issuers()


def get_first_jwt_issuer():
    """
    Retrieves the first issuer in the JWT_ISSUERS list.

    As mentioned above, support for multiple JWT_ISSUERS is deprecated. They
    are currently used only to distinguish the "ISSUER" field across sites.
    So in many cases, we just need the first issuer value.
    """
    return get_jwt_issuers()[0]
