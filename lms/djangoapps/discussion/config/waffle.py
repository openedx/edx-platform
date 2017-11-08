"""
This module contains various configuration settings via
waffle switches for the Discussions app.
"""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace, WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = u'discussions'

# Switches
FORUM_RESPONSE_NOTIFICATIONS = u'forum_response_notifications'

SEND_NOTIFICATIONS_FOR_COURSE = CourseWaffleFlag(
    waffle_namespace=WaffleFlagNamespace(name=WAFFLE_NAMESPACE),
    flag_name=u'send_notifications_for_course',
    flag_undefined_default=False
)


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Discussions.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Discussions: ')
