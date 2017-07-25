"""
Unified course experience settings and helper methods.
"""
from django.utils.translation import ugettext as _

from openedx.core.djangoapps.util.user_messages import UserMessageCollection
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace


# Namespace for course experience waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='course_experience')

# Waffle flag to enable the separate course outline page and full width content.
COURSE_OUTLINE_PAGE_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'course_outline_page', flag_undefined_default=True)

# Waffle flag to enable a single unified "Course" tab.
UNIFIED_COURSE_TAB_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'unified_course_tab')

# Waffle flag to enable the sock on the footer of the home and courseware pages
DISPLAY_COURSE_SOCK_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'display_course_sock')

# Waffle flag to let learners access a course before its start date
COURSE_PRE_START_ACCESS_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'pre_start_access')

# Waffle flag to enable a review page link from the unified home page
SHOW_REVIEWS_TOOL_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'show_reviews_tool')


def course_home_page_title(course):  # pylint: disable=unused-argument
    """
    Returns the title for the course home page.
    """
    return _('Course')


def default_course_url_name(course_id):
    """
    Returns the default course URL name for the current user.

    Arguments:
        course_id (CourseKey): The course id of the current course.
    """
    if COURSE_OUTLINE_PAGE_FLAG.is_enabled(course_id):
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


class CourseHomeMessages(UserMessageCollection):
    """
    This set of messages appear above the outline on the course home page.
    """
    NAMESPACE = 'course_home_level_messages'

    @classmethod
    def get_namespace(self):
        """
        Returns the namespace of the message collection.
        """
        return self.NAMESPACE
