"""
This module contains configuration settings via waffle flags
for the Video Pipeline app.
"""
from openedx.core.djangoapps.waffle_utils import WaffleFlagNamespace, CourseWaffleFlag

# Videos Namespace
WAFFLE_NAMESPACE = 'videos'

# Waffle flag telling whether youtube is deprecated.
DEPRECATE_YOUTUBE = 'deprecate_youtube'


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for Videos.
    """
    namespace = WaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Videos: ')
    return {
        DEPRECATE_YOUTUBE: CourseWaffleFlag(
            waffle_namespace=namespace,
            flag_name=DEPRECATE_YOUTUBE
        )
    }
