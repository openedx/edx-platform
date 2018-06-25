"""
Feature toggle code for oauth_dispatch.
"""

from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace, WaffleSwitch

WAFFLE_NAMESPACE = 'oauth2'
OAUTH2_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)
UNEXPIRED_RESTRICTED_APPLICATIONS = WaffleSwitch(OAUTH2_SWITCHES, 'unexpired_restricted_applications')
