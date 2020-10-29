"""
Unified course experience settings and helper methods.
"""


from django.utils.translation import ugettext as _

from lms.djangoapps.experiments.flags import ExperimentWaffleFlag
from openedx.core.djangoapps.util.user_messages import UserMessageCollection
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlag, WaffleFlagNamespace

# Namespace for course experience waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='course_experience')

# Waffle flag to enable the separate course outline page and full width content.
COURSE_OUTLINE_PAGE_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'course_outline_page', flag_undefined_default=True)

# Waffle flag to enable a single unified "Course" tab.
UNIFIED_COURSE_TAB_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'unified_course_tab', flag_undefined_default=True)

# Waffle flag to enable the sock on the footer of the home and courseware pages.
DISPLAY_COURSE_SOCK_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'display_course_sock')

# Waffle flag to let learners access a course before its start date.
COURSE_PRE_START_ACCESS_FLAG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'pre_start_access')

# Waffle flag to enable a review page link from the unified home page.
# .. toggle_name: course_experience.show_reviews_tool
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Used with our integration with CourseTalk to display reviews for a course.
# .. toggle_category: course_experience
# .. toggle_use_cases: monitored_rollout
# .. toggle_creation_date: 2017-06-19
# .. toggle_expiration_date: ???
# .. toggle_warnings: We are no longer integrating with CourseTalk, so this probably should be deprecated and the code for reviews should be removed.
# .. toggle_tickets: DEPR-48
# .. toggle_status: unsupported
SHOW_REVIEWS_TOOL_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'show_reviews_tool')

# Waffle flag to enable the setting of course goals.
# .. toggle_name: course_experience.enable_course_goals
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Used to determine whether or not to use course goals for the particular course.
# .. toggle_category: course_experience
# .. toggle_use_cases: opt_out, monitored_rollout
# .. toggle_creation_date: 2017-09-11
# .. toggle_expiration_date: ???
# .. toggle_warnings: N/A
# .. toggle_tickets: N/A
# .. toggle_status: supported
ENABLE_COURSE_GOALS = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'enable_course_goals')

# Waffle flag to control the display of the hero
SHOW_UPGRADE_MSG_ON_COURSE_HOME = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'show_upgrade_msg_on_course_home')

# Waffle flag to control the display of the upgrade deadline message
UPGRADE_DEADLINE_MESSAGE = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'upgrade_deadline_message')

# Waffle flag to switch between the 'welcome message' and 'latest update' on the course home page.
# .. toggle_name: course_experience.latest_update
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Used to switch between 'welcome message' and 'latest update' on the course home page.
# .. toggle_category: course_experience
# .. toggle_use_cases: opt_out
# .. toggle_creation_date: 2017-09-11
# .. toggle_expiration_date: ???
# .. toggle_warnings: This is meant to be configured using waffle_utils course override only.  Either do not create the actual waffle flag, or be sure to unset the flag even for Superusers.
# .. toggle_tickets: N/A
# .. toggle_status: supported
LATEST_UPDATE_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'latest_update')

# Waffle flag to enable the use of Bootstrap for course experience pages
USE_BOOTSTRAP_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'use_bootstrap', flag_undefined_default=True)

# Waffle flag to enable anonymous access to a course
SEO_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='seo')
COURSE_ENABLE_UNENROLLED_ACCESS_FLAG = CourseWaffleFlag(SEO_WAFFLE_FLAG_NAMESPACE, 'enable_anonymous_courseware_access')

# Waffle flag to enable relative dates for course content
RELATIVE_DATES_FLAG = ExperimentWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'relative_dates', experiment_id=17)

# Waffle flag to enable user calendar syncing
CALENDAR_SYNC_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'calendar_sync')


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
    def get_namespace(cls):
        """
        Returns the namespace of the message collection.
        """
        return cls.NAMESPACE
