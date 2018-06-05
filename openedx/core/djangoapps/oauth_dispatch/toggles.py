"""
Feature toggle code for oauth_dispatch.
"""

from edx_rest_framework_extensions.config import SWITCH_ENFORCE_JWT_SCOPES

from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace, WaffleSwitch

WAFFLE_NAMESPACE = 'oauth2'
OAUTH2_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)
ENFORCE_JWT_SCOPES = WaffleSwitch(OAUTH2_SWITCHES, SWITCH_ENFORCE_JWT_SCOPES)
