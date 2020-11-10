"""
Views for the course home page.
"""


import six
from django.conf import settings
from django.template.context_processors import csrf
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import can_self_enroll_in_course, get_course_info_section, get_course_with_access
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.course_goals.api import (
    get_course_goal,
    get_course_goal_options,
    get_goal_api_url,
    has_course_goal_permission
)
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from lms.djangoapps.courseware.utils import can_show_verified_upgrade, verified_upgrade_deadline_link
from lms.djangoapps.courseware.views.views import CourseTabView
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangoapps.util.maintenance_banner import add_maintenance_banner
from openedx.features.course_duration_limits.access import generate_course_expired_fragment
from openedx.features.course_experience.course_tools import CourseToolsPluginManager
from openedx.features.discounts.utils import get_first_purchase_offer_banner_fragment
from openedx.features.discounts.utils import format_strikeout_price
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.util.views import ensure_valid_course_key
from xmodule.course_module import COURSE_VISIBILITY_PUBLIC, COURSE_VISIBILITY_PUBLIC_OUTLINE

from .. import (
    COURSE_ENABLE_UNENROLLED_ACCESS_FLAG,
    LATEST_UPDATE_FLAG,
    SHOW_UPGRADE_MSG_ON_COURSE_HOME,
)
from ..utils import get_course_outline_block_tree, get_resume_block
from .course_dates import CourseDatesFragmentView
from .course_home_messages import CourseHomeMessageFragmentView
from .course_outline import CourseOutlineFragmentView
from .course_sock import CourseSockFragmentView
from .latest_update import LatestUpdateFragmentView
from .welcome_message import WelcomeMessageFragmentView

EMPTY_HANDOUTS_HTML = u'<ol></ol>'


class CourseHomeView(CourseTabView):
    """
    The home page for a course.
    """
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    @method_decorator(add_maintenance_banner)
    def get(self, request, course_id, **kwargs):
        """
        Displays the home page for the specified course.
        """
        return super(CourseHomeView, self).get(request, course_id, 'courseware', **kwargs)

    def render_to_fragment(self, request, course=None, tab=None, **kwargs):
        course_id = six.text_type(course.id)
        home_fragment_view = CourseHomeFragmentView()
        return home_fragment_view.render_to_fragment(request, course_id=course_id, **kwargs)


class CourseHomeFragmentView(EdxFragmentView):
    """
    A fragment to render the home page for a course.
    """

    def _get_resume_course_info(self, request, course_id):
        """
        Returns information relevant to resume course functionality.

        Returns a tuple: (has_visited_course, resume_course_url)
            has_visited_course: True if the user has ever visted the course, False otherwise.
            resume_course_url: The URL of the 'resume course' block if the user has visited the course,
                otherwise the URL of the course root.

        """
        course_outline_root_block = get_course_outline_block_tree(request, course_id, request.user)
        resume_block = get_resume_block(course_outline_root_block) if course_outline_root_block else None
        has_visited_course = bool(resume_block)
        if resume_block:
            resume_course_url = resume_block['lms_web_url']
        else:
            resume_course_url = course_outline_root_block['lms_web_url'] if course_outline_root_block else None

        return has_visited_course, resume_course_url

    def _get_course_handouts(self, request, course):
        """
        Returns the handouts for the specified course.
        """
        handouts = get_course_info_section(request, request.user, course, 'handouts')
        if not handouts or handouts == EMPTY_HANDOUTS_HTML:
            return None
        return handouts

    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Renders the course's home page as a fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key)

        # Render the course dates as a fragment
        dates_fragment = CourseDatesFragmentView().render_to_fragment(request, course_id=course_id, **kwargs)

        # Render the full content to enrolled users, as well as to course and global staff.
        # Unenrolled users who are not course or global staff are given only a subset.
        enrollment = CourseEnrollment.get_enrollment(request.user, course_key)
        user_access = {
            'is_anonymous': request.user.is_anonymous,
            'is_enrolled': enrollment and enrollment.is_active,
            'is_staff': has_access(request.user, 'staff', course_key),
        }

        allow_anonymous = COURSE_ENABLE_UNENROLLED_ACCESS_FLAG.is_enabled(course_key)
        allow_public = allow_anonymous and course.course_visibility == COURSE_VISIBILITY_PUBLIC
        allow_public_outline = allow_anonymous and course.course_visibility == COURSE_VISIBILITY_PUBLIC_OUTLINE

        # Set all the fragments
        outline_fragment = None
        update_message_fragment = None
        course_sock_fragment = None
        offer_banner_fragment = None
        course_expiration_fragment = None
        has_visited_course = None
        resume_course_url = None
        handouts_html = None

        course_overview = CourseOverview.get_from_id(course.id)
        if user_access['is_enrolled'] or user_access['is_staff']:
            outline_fragment = CourseOutlineFragmentView().render_to_fragment(
                request, course_id=course_id, **kwargs
            )
            if LATEST_UPDATE_FLAG.is_enabled(course_key):
                update_message_fragment = LatestUpdateFragmentView().render_to_fragment(
                    request, course_id=course_id, **kwargs
                )
            else:
                update_message_fragment = WelcomeMessageFragmentView().render_to_fragment(
                    request, course_id=course_id, **kwargs
                )
            course_sock_fragment = CourseSockFragmentView().render_to_fragment(
                request, course=course, **kwargs
            )
            has_visited_course, resume_course_url = self._get_resume_course_info(request, course_id)
            handouts_html = self._get_course_handouts(request, course)
            offer_banner_fragment = get_first_purchase_offer_banner_fragment(
                request.user,
                course_overview
            )
            course_expiration_fragment = generate_course_expired_fragment(
                request.user,
                course_overview
            )
        elif allow_public_outline or allow_public:
            outline_fragment = CourseOutlineFragmentView().render_to_fragment(
                request, course_id=course_id, user_is_enrolled=False, **kwargs
            )
            course_sock_fragment = CourseSockFragmentView().render_to_fragment(request, course=course, **kwargs)
            if allow_public:
                handouts_html = self._get_course_handouts(request, course)
        else:
            # Redirect the user to the dashboard if they are not enrolled and
            # this is a course that does not support direct enrollment.
            if not can_self_enroll_in_course(course_key):
                raise CourseAccessRedirect(reverse('dashboard'))

        # Get the course tools enabled for this user and course
        course_tools = CourseToolsPluginManager.get_enabled_course_tools(request, course_key)

        # Check if the user can access the course goal functionality
        has_goal_permission = has_course_goal_permission(request, course_id, user_access)

        # Grab the current course goal and the acceptable course goal keys mapped to translated values
        current_goal = get_course_goal(request.user, course_key)
        goal_options = get_course_goal_options()

        # Get the course goals api endpoint
        goal_api_url = get_goal_api_url(request)

        # Grab the course home messages fragment to render any relevant django messages
        course_home_message_fragment = CourseHomeMessageFragmentView().render_to_fragment(
            request, course_id=course_id, user_access=user_access, **kwargs
        )

        # Get info for upgrade messaging
        upgrade_price = None
        upgrade_url = None
        has_discount = False

        # TODO Add switch to control deployment
        if SHOW_UPGRADE_MSG_ON_COURSE_HOME.is_enabled(course_key) and can_show_verified_upgrade(
            request.user,
            enrollment,
            course
        ):
            upgrade_url = verified_upgrade_deadline_link(request.user, course_id=course_key)
            upgrade_price, has_discount = format_strikeout_price(request.user, course_overview)

        show_search = (
            settings.FEATURES.get('ENABLE_COURSEWARE_SEARCH') or
            (settings.FEATURES.get('ENABLE_COURSEWARE_SEARCH_FOR_COURSE_STAFF') and user_access['is_staff'])
        )
        # Render the course home fragment
        context = {
            'request': request,
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'course_key': course_key,
            'outline_fragment': outline_fragment,
            'handouts_html': handouts_html,
            'course_home_message_fragment': course_home_message_fragment,
            'offer_banner_fragment': offer_banner_fragment,
            'course_expiration_fragment': course_expiration_fragment,
            'has_visited_course': has_visited_course,
            'resume_course_url': resume_course_url,
            'course_tools': course_tools,
            'dates_fragment': dates_fragment,
            'username': request.user.username,
            'goal_api_url': goal_api_url,
            'has_goal_permission': has_goal_permission,
            'goal_options': goal_options,
            'current_goal': current_goal,
            'update_message_fragment': update_message_fragment,
            'course_sock_fragment': course_sock_fragment,
            'disable_courseware_js': True,
            'uses_bootstrap': True,
            'upgrade_price': upgrade_price,
            'upgrade_url': upgrade_url,
            'has_discount': has_discount,
            'show_search': show_search,
        }
        html = render_to_string('course_experience/course-home-fragment.html', context)
        return Fragment(html)
