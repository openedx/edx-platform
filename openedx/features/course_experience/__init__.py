"""
Unified course experience settings and helper methods.
"""
import crum
from django.utils.translation import ugettext as _
from edx_django_utils.monitoring import set_custom_attribute
from waffle import flag_is_active

from lms.djangoapps.experiments.flags import ExperimentWaffleFlag
from openedx.core.djangoapps.util.user_messages import UserMessageCollection
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlag, WaffleFlagNamespace

# Namespace for course experience waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='course_experience')


class DefaultTrueWaffleFlagNamespace(WaffleFlagNamespace):
    """
    This is a temporary class to help deprecate/remove ``flag_undefined_default``.

    TODO: TNL-7061: Perform the actual clean-up required to remove these flags
        and refactor/fix any tests that shouldn't be removed.

    """
    def is_flag_active(self, flag_name, check_before_waffle_callback=None):
        """
        Overrides is_flag_active, and returns and caches whether the provided flag is active.

        If the flag value is already cached in the request, it is returned.
        If the flag doesn't exist, always returns default of True.

        Note: This is a similified version of the method it overrides, that
        hard codes the default to True, and skips the call back used for
        course overrides:
        https://github.com/edx/edx-platform/blob/df9be8c678f8266e2e5710513c74deca14c4527c/openedx/core/djangoapps/waffle_utils/__init__.py#L229-L305

        """
        # Import is placed here to avoid model import at project startup.
        from waffle.models import Flag

        # validate arguments
        namespaced_flag_name = self._namespaced_name(flag_name)
        value = self._cached_flags.get(namespaced_flag_name)
        if value is None:

            # determine if the flag is undefined in waffle
            try:
                Flag.objects.get(name=namespaced_flag_name)
            except Flag.DoesNotExist:
                # default to True if not defined
                value = True

            if value is None:
                request = crum.get_current_request()
                if request:
                    value = flag_is_active(request, namespaced_flag_name)
                else:
                    set_custom_attribute('warn_flag_no_request', True)
                    # Return the default value if not in a request context.
                    # Same as the original implementation
                    self._set_waffle_flag_attribute(namespaced_flag_name, value)
                    return True

            self._cached_flags[namespaced_flag_name] = value

        self._set_waffle_flag_attribute(namespaced_flag_name, value)
        return value


DEFAULT_TRUE_WAFFLE_FLAG_NAMESPACE = DefaultTrueWaffleFlagNamespace(name='course_experience')

# Waffle flag to enable the separate course outline page and full width content.
# NOTE: The special namespace makes the default True and skips checking course overrides.
# TODO: TNL-7061: Perform the actual clean-up required to remove this flag.
COURSE_OUTLINE_PAGE_FLAG = CourseWaffleFlag(DEFAULT_TRUE_WAFFLE_FLAG_NAMESPACE, 'course_outline_page', __name__)

# Waffle flag to enable a single unified "Course" tab.
# NOTE: The special namespace makes the default True and skips checking course overrides.
# TODO: TNL-7061: Perform the actual clean-up required to remove this flag.
UNIFIED_COURSE_TAB_FLAG = CourseWaffleFlag(DEFAULT_TRUE_WAFFLE_FLAG_NAMESPACE, 'unified_course_tab', __name__)

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
# .. toggle_warnings: This is meant to be configured using waffle_utils course override only. Either do not create the
#   actual waffle flag, or be sure to unset the flag even for Superusers.
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
