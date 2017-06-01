"""
Unified course experience settings and helper methods.
"""
import waffle

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace
from request_cache.middleware import RequestCache

# Waffle flag to enable the full screen course content view along with a unified
# course home page.
# NOTE: This is the only legacy flag that does not use the namespace.
UNIFIED_COURSE_VIEW_FLAG = 'unified_course_view'

# Namespace for course experience waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='course_experience')

# Waffle flag to enable a single unified "Course" tab.
UNIFIED_COURSE_TAB_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'unified_course_tab')


def default_course_url_name(request=None):
    """
    Returns the default course URL name for the current user.
    """
    if waffle.flag_is_active(request or RequestCache.get_current_request(), UNIFIED_COURSE_VIEW_FLAG):
        return 'openedx.course_experience.course_home'
    else:
        return 'courseware'


def course_home_url_name(course_key):
    """
    Returns the course home page's URL name for the current user.

    Arguments:
        course_key (CourseKey): The course key for which the home url is being
            requested.

    """
    if UNIFIED_COURSE_TAB_FLAG.is_enabled(course_key):
        return 'openedx.course_experience.course_home'
    else:
        return 'info'
