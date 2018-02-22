"""
This module contains various configuration settings via
waffle switches for the contentstore app.
"""
from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = u'studio'

# Switches
ENABLE_ACCESSIBILITY_POLICY_PAGE = u'enable_policy_page'
ENABLE_ASSETS_SEARCH = u'enable_assets_search'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Studio pages.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Studio: ')
