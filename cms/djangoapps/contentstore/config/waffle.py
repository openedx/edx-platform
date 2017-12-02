"""
This module contains various configuration settings via
waffle switches for the contentstore app.
"""
from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = u'accessibility'

# Switches
ENABLE_ACCESSIBILITY_POLICY_PAGE = u'enable_policy_page'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Accessibility Accomodation Request Page.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Accessibility: ')
