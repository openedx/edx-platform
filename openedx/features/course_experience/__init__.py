"""
Unified course experience settings and helper methods.
"""
import crum
from django.utils.translation import ugettext as _
from edx_django_utils.monitoring import set_custom_attribute
from waffle import flag_is_active  # lint-amnesty, pylint: disable=invalid-django-waffle-import

from edx_toggles.toggles import LegacyWaffleFlag, LegacyWaffleFlagNamespace
from openedx.core.djangoapps.util.user_messages import UserMessageCollection
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Namespace for course experience waffle flags.
WAFFLE_FLAG_NAMESPACE = LegacyWaffleFlagNamespace(name='course_experience')

COURSE_EXPERIENCE_WAFFLE_FLAG_NAMESPACE = LegacyWaffleFlagNamespace(name='course_experience')

# Waffle flag to disable the separate course outline page and full width content.
DISABLE_COURSE_OUTLINE_PAGE_FLAG = CourseWaffleFlag(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    COURSE_EXPERIENCE_WAFFLE_FLAG_NAMESPACE, 'disable_course_outline_page', __name__
)

# Waffle flag to enable a single unified "Course" tab.
DISABLE_UNIFIED_COURSE_TAB_FLAG = CourseWaffleFlag(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    COURSE_EXPERIENCE_WAFFLE_FLAG_NAMESPACE, 'disable_unified_course_tab', __name__
)

# Waffle flag to enable the sock on the footer of the home and courseware pages.
DISPLAY_COURSE_SOCK_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'display_course_sock', __name__)  # lint-amnesty, pylint: disable=toggle-missing-annotation

# Waffle flag to let learners access a course before its start date.
COURSE_PRE_START_ACCESS_FLAG = LegacyWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'pre_start_access', __name__)  # lint-amnesty, pylint: disable=toggle-missing-annotation

# .. toggle_name: course_experience.enable_course_goals
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Used to determine whether or not to use course goals for the particular course.
# .. toggle_use_cases: opt_out, temporary
# .. toggle_creation_date: 2017-09-11
# .. toggle_target_removal_date: None
# .. toggle_warnings: This temporary feature toggle does not have a target removal date.
ENABLE_COURSE_GOALS = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'enable_course_goals', __name__)  # lint-amnesty, pylint: disable=toggle-missing-annotation

# Waffle flag to control the display of the hero
SHOW_UPGRADE_MSG_ON_COURSE_HOME = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'show_upgrade_msg_on_course_home', __name__)  # lint-amnesty, pylint: disable=toggle-missing-annotation

# Waffle flag to control the display of the upgrade deadline message
UPGRADE_DEADLINE_MESSAGE = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'upgrade_deadline_message', __name__)  # lint-amnesty, pylint: disable=toggle-missing-annotation

# .. toggle_name: course_experience.latest_update
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Used to switch between 'welcome message' and 'latest update' on the course home page.
# .. toggle_use_cases: opt_out, temporary
# .. toggle_creation_date: 2017-09-11
# .. toggle_target_removal_date: None
# .. toggle_warnings: This is meant to be configured using waffle_utils course override only. Either do not create the
#   actual waffle flag, or be sure to unset the flag even for Superusers. This is no longer used in the learning MFE
#   and can be removed when the outline tab is fully moved to the learning MFE.
LATEST_UPDATE_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'latest_update', __name__)  # lint-amnesty, pylint: disable=toggle-missing-annotation

# Waffle flag to enable anonymous access to a course
SEO_WAFFLE_FLAG_NAMESPACE = LegacyWaffleFlagNamespace(name='seo')
COURSE_ENABLE_UNENROLLED_ACCESS_FLAG = CourseWaffleFlag(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    SEO_WAFFLE_FLAG_NAMESPACE,
    'enable_anonymous_courseware_access',
    __name__,
)

# .. toggle_name: course_experience.relative_dates
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable relative dates for course content. A 'Dates' tab will be visible in the
#   course view showing key course dates. Was previously an ExperimentWaffleFlag with experiment_id=17.
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2020-02-10
# .. toggle_warnings: To set a relative due date for self-paced courses, the weeks_to_complete field for a course run
#   needs to be set. Currently it can be set through the publisher app.
# .. toggle_tickets: https://openedx.atlassian.net/browse/AA-27
RELATIVE_DATES_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'relative_dates', __name__)  # lint-amnesty, pylint: disable=toggle-missing-annotation

# .. toggle_name: course_experience.calendar_sync
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This course flag enables a course tool (which is a tool that is added on a course home page)
#   that sends course assignment calendars to course students, whenever they click on the "Subscribe to calendar
#   updates" button. The email contains an ics attachment that students can then use to sync with their own calendar
#   apps.
# .. toggle_warnings: For this toggle to have an effect, the RELATIVE_DATES_FLAG toggle must be enabled, too.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-01-26
# .. toggle_target_removal_date: 2021-04-26
# .. toggle_tickets: https://openedx.atlassian.net/browse/AA-36
CALENDAR_SYNC_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'calendar_sync', __name__)  # lint-amnesty, pylint: disable=toggle-missing-annotation


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
