"""
Feature toggle code for oauth_dispatch.
"""


from edx_rest_framework_extensions.config import OAUTH_TOGGLE_NAMESPACE, SWITCH_ENFORCE_JWT_SCOPES

from openedx.core.djangoapps.waffle_utils import WaffleSwitch, WaffleSwitchNamespace


ENFORCE_JWT_SCOPES = WaffleSwitch(WaffleSwitchNamespace(name=OAUTH_TOGGLE_NAMESPACE), SWITCH_ENFORCE_JWT_SCOPES)
