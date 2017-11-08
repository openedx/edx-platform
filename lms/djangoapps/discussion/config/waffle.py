"""
This module contains various configuration settings via
waffle switches for the Discussions app.
"""
from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = u'discussions'

# Switches
FORUM_RESPONSE_NOTIFICATIONS = u'forum_response_notifications'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Discussions.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Discussions: ')
