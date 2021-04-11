"""
Unified course experience settings and helper methods.
"""
import crum
from django.utils.translation import ugettext as _
from edx_django_utils.monitoring import set_custom_attribute
from waffle import flag_is_active

from edx_toggles.toggles import WaffleFlag, WaffleFlagNamespace
from lms.djangoapps.experiments.flags import ExperimentWaffleFlag
from openedx.core.djangoapps.util.user_messages import UserMessageCollection
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Namespace for course experience waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='course_experience')

COURSE_EXPERIENCE_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='course_experience')

# Waffle flag to disable the separate course outline page and full width content.
DISABLE_COURSE_OUTLINE_PAGE_FLAG = CourseWaffleFlag(
    COURSE_EXPERIENCE_WAFFLE_FLAG_NAMESPACE, 'disable_course_outline_page', __name__
)

# Waffle flag to enable a single unified "Course" tab.
DISABLE_UNIFIED_COURSE_TAB_FLAG = CourseWaffleFlag(
    COURSE_EXPERIENCE_WAFFLE_FLAG_NAMESPACE, 'disable_unified_course_tab', __name__
)

# Waffle flag to enable the sock on the footer of the home and courseware pages.
DISPLAY_COURSE_SOCK_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'display_course_sock', __name__)

# Waffle flag to let learners access a course before its start date.
COURSE_PRE_START_ACCESS_FLAG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'pre_start_access', __name__)

# Waffle flag to enable a review page link from the unified home page.
# .. toggle_name: course_experience.show_reviews_tool
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Used with our integration with CourseTalk to display reviews for a course.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2017-06-19
# .. toggle_target_removal_date: None
# .. toggle_warnings: We are no longer integrating with CourseTalk, so this probably should be deprecated and the code
#   for reviews should be removed. This temporary feature toggle should have a target removal date.
# .. toggle_tickets: DEPR-48
SHOW_REVIEWS_TOOL_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'show_reviews_tool', __name__)

# Waffle flag to enable the setting of course goals.
# .. toggle_name: course_experience.enable_course_goals
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Used to determine whether or not to use course goals for the particular course.
# .. toggle_use_cases: opt_out, temporary
# .. toggle_creation_date: 2017-09-11
# .. toggle_target_removal_date: None
# .. toggle_warnings: This temporary feature toggle does not have a target removal date.
# .. toggle_tickets: None
ENABLE_COURSE_GOALS = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'enable_course_goals', __name__)

# Waffle flag to control the display of the hero
SHOW_UPGRADE_MSG_ON_COURSE_HOME = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'show_upgrade_msg_on_course_home', __name__)

# Waffle flag to control the display of the upgrade deadline message
UPGRADE_DEADLINE_MESSAGE = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'upgrade_deadline_message', __name__)

# Waffle flag to switch between the 'welcome message' and 'latest update' on the course home page.
# .. toggle_name: course_experience.latest_update
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Used to switch between 'welcome message' and 'latest update' on the course home page.
# .. toggle_use_cases: opt_out
# .. toggle_creation_date: 2017-09-11
# .. toggle_target_removal_date: None
# .. toggle_warnings: This is meant to be configured using waffle_utils course override only. Either do not create the
#   actual waffle flag, or be sure to unset the flag even for Superusers.
# .. toggle_tickets: None
LATEST_UPDATE_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'latest_update', __name__)

# Waffle flag to enable anonymous access to a course
SEO_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='seo')
COURSE_ENABLE_UNENROLLED_ACCESS_FLAG = CourseWaffleFlag(
    SEO_WAFFLE_FLAG_NAMESPACE,
    'enable_anonymous_courseware_access',
    __name__,
)

# Waffle flag to enable relative dates for course content
RELATIVE_DATES_FLAG = ExperimentWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'relative_dates', __name__, experiment_id=17)

# Waffle flag to enable user calendar syncing
CALENDAR_SYNC_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'calendar_sync', __name__)


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
    if DISABLE_COURSE_OUTLINE_PAGE_FLAG.is_enabled(course_id):
        return 'courseware'
    return 'openedx.course_experience.course_home'


def course_home_url_name(course_key):
    """
    Returns the course home page's URL name for the current user.

    Arguments:
        course_key (CourseKey): The course key for which the home url is being
            requested.

    """
    if DISABLE_UNIFIED_COURSE_TAB_FLAG.is_enabled(course_key):
        return 'info'
    return 'openedx.course_experience.course_home'


class CourseHomeMessages(UserMessageCollection):
    """
    This set of messages appear above the outline on the course home page.
    """
    NAMESPACE = 'course_home_level_messages'

    @classmethod
    def get_namespace(cls):
        """
        Returns the namespace of the message collection.
        """
        return cls.NAMESPACE
