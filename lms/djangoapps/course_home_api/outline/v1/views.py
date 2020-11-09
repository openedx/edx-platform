"""
Outline Tab Views
"""

from django.http.response import Http404
from django.urls import reverse
from django.utils.translation import gettext as _
from edx_django_utils import monitoring as monitoring_utils
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import APIException, ParseError
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from completion.exceptions import UnavailableCompletionData
from completion.utilities import get_key_to_last_completed_block
from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.course_goals.api import (add_course_goal, get_course_goal, get_course_goal_text,
                                             has_course_goal_permission, valid_course_goals_ordered)
from lms.djangoapps.course_home_api.outline.v1.serializers import OutlineTabSerializer
from lms.djangoapps.course_home_api.toggles import (course_home_mfe_dates_tab_is_active,
                                                    course_home_mfe_outline_tab_is_active)
from lms.djangoapps.course_home_api.utils import get_microfrontend_url
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.context_processor import user_timezone_locale_prefs
from lms.djangoapps.courseware.courses import get_course_date_blocks, get_course_info_section, get_course_with_access
from lms.djangoapps.courseware.date_summary import TodaysDate
from lms.djangoapps.courseware.masquerade import setup_masquerade
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_duration_limits.access import generate_course_expired_message
from openedx.features.course_experience import COURSE_ENABLE_UNENROLLED_ACCESS_FLAG
from openedx.features.course_experience.course_tools import CourseToolsPluginManager
from openedx.features.course_experience.course_updates import (
    dismiss_current_update_for_user, get_current_update_for_user,
)
from openedx.features.course_experience.utils import get_course_outline_block_tree
from openedx.features.discounts.utils import generate_offer_html
from common.djangoapps.student.models import CourseEnrollment
from xmodule.course_module import COURSE_VISIBILITY_PUBLIC, COURSE_VISIBILITY_PUBLIC_OUTLINE
from xmodule.modulestore.django import modulestore


class UnableToDismissWelcomeMessage(APIException):
    status_code = 400
    default_detail = 'Unable to dismiss welcome message.'
    default_code = 'unable_to_dismiss_welcome_message'


class UnableToSaveCourseGoal(APIException):
    status_code = 400
    default_detail = 'Unable to save course goal'
    default_code = 'unable_to_save_course_goal'


class OutlineTabView(RetrieveAPIView):
    """
    **Use Cases**

        Request details for the Outline Tab

    **Example Requests**

        GET api/course_home/v1/outline/{course_key}

    **Response Values**

        Body consists of the following fields:

        course_blocks:
            blocks: List of serialized Course Block objects. Each serialization has the following fields:
                id: (str) The usage ID of the block.
                type: (str) The type of block. Possible values the names of any
                    XBlock type in the system, including custom blocks. Examples are
                    course, chapter, sequential, vertical, html, problem, video, and
                    discussion.
                display_name: (str) The display name of the block.
                lms_web_url: (str) The URL to the navigational container of the
                    xBlock on the web LMS.
                children: (list) If the block has child blocks, a list of IDs of
                    the child blocks.
                resume_block: (bool) Whether the block is the resume block
        course_goals:
            goal_options: (list) A list of goals where each goal is represented as a tuple (goal_key, goal_string)
            selected_goal:
                key: (str) The unique id given to the user's selected goal.
                text: (str) The display text for the user's selected goal.
        course_tools: List of serialized Course Tool objects. Each serialization has the following fields:
            analytics_id: (str) The unique id given to the tool.
            title: (str) The display title of the tool.
            url: (str) The link to access the tool.
        dates_banner_info: (obj)
            content_type_gating_enabled: (bool) Whether content type gating is enabled for this enrollment.
            missed_deadlines: (bool) Whether the user has missed any graded content deadlines for the given course.
            missed_gated_content: (bool) Whether the user has missed any gated content for the given course.
            verified_upgrade_link: (str) The URL to ecommerce IDA for purchasing the verified upgrade.
        dates_widget:
            course_date_blocks: List of serialized Course Dates objects. Each serialization has the following fields:
                complete: (bool) Meant to only be used by assignments. Indicates completeness for an
                assignment.
                date: (datetime) The date time corresponding for the event
                date_type: (str) The type of date (ex. course-start-date, assignment-due-date, etc.)
                description: (str) The description for the date event
                learner_has_access: (bool) Indicates if the learner has access to the date event
                link: (str) An absolute link to content related to the date event
                    (ex. verified link or link to assignment)
                title: (str) The title of the date event
            dates_tab_link: (str) The URL to the Dates Tab
            user_timezone: (str) The timezone of the given user
        enroll_alert:
            can_enroll: (bool) Whether the user can enroll in the given course
            extra_text: (str)
        handouts_html: (str) Raw HTML for the handouts section of the course info
        has_ended: (bool) Indicates whether course has ended
        resume_course:
            has_visited_course: (bool) Whether the user has ever visited the course
            url: (str) The display name of the course block to resume
        welcome_message_html: (str) Raw HTML for the course updates banner

    **Returns**

        * 200 on success with above fields.
        * 403 if the user is not authenticated.
        * 404 if the course is not available or cannot be seen.

    """

    permission_classes = (IsAuthenticated,)
    serializer_class = OutlineTabSerializer

    def get(self, request, *args, **kwargs):
        course_key_string = kwargs.get('course_key_string')
        course_key = CourseKey.from_string(course_key_string)
        course_usage_key = modulestore().make_course_usage_key(course_key)

        if not course_home_mfe_outline_tab_is_active(course_key):
            raise Http404

        # Enable NR tracing for this view based on course
        monitoring_utils.set_custom_attribute('course_id', course_key_string)
        monitoring_utils.set_custom_attribute('user_id', request.user.id)
        monitoring_utils.set_custom_attribute('is_staff', request.user.is_staff)

        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=False)

        _masquerade, request.user = setup_masquerade(
            request,
            course_key,
            staff_access=has_access(request.user, 'staff', course_key),
            reset_masquerade_data=True,
        )

        course_overview = CourseOverview.get_from_id(course_key)
        enrollment = CourseEnrollment.get_enrollment(request.user, course_key)
        allow_anonymous = COURSE_ENABLE_UNENROLLED_ACCESS_FLAG.is_enabled(course_key)
        allow_public = allow_anonymous and course.course_visibility == COURSE_VISIBILITY_PUBLIC
        allow_public_outline = allow_anonymous and course.course_visibility == COURSE_VISIBILITY_PUBLIC_OUTLINE
        is_enrolled = enrollment and enrollment.is_active
        is_staff = bool(has_access(request.user, 'staff', course_key))
        show_enrolled = is_enrolled or is_staff

        show_handouts = show_enrolled or allow_public
        handouts_html = get_course_info_section(request, request.user, course, 'handouts') if show_handouts else ''

        # TODO: TNL-7185 Legacy: Refactor to return the offer & expired data and format the message in the MFE
        offer_html = show_enrolled and generate_offer_html(request.user, course_overview)
        course_expired_html = show_enrolled and generate_course_expired_message(request.user, course_overview)

        welcome_message_html = show_enrolled and get_current_update_for_user(request, course)

        enroll_alert = {
            'can_enroll': True,
            'extra_text': None,
        }
        if not show_enrolled:
            if CourseMode.is_masters_only(course_key):
                enroll_alert['can_enroll'] = False
                enroll_alert['extra_text'] = _('Please contact your degree administrator or '
                                               'edX Support if you have questions.')
            elif course.invitation_only:
                enroll_alert['can_enroll'] = False

        course_tools = CourseToolsPluginManager.get_enabled_course_tools(request, course_key)
        date_blocks = get_course_date_blocks(course, request.user, request, num_assignments=1)

        # User locale settings
        user_timezone_locale = user_timezone_locale_prefs(request)
        user_timezone = user_timezone_locale['user_timezone']

        dates_tab_link = request.build_absolute_uri(reverse('dates', args=[course.id]))
        if course_home_mfe_dates_tab_is_active(course.id):
            dates_tab_link = get_microfrontend_url(course_key=course.id, view_name='dates')

        course_blocks = None
        if show_enrolled or allow_public or allow_public_outline:
            outline_user = request.user if show_enrolled else None
            course_blocks = get_course_outline_block_tree(request, course_key_string, outline_user)

        resume_course = {
            'has_visited_course': False,
            'url': None,
        }
        if show_enrolled:
            try:
                resume_block = get_key_to_last_completed_block(request.user, course.id)
                resume_course['has_visited_course'] = True
            except UnavailableCompletionData:
                resume_block = course_usage_key
            resume_path = reverse('jump_to', kwargs={
                'course_id': course_key_string,
                'location': str(resume_block)
            })
            resume_course['url'] = request.build_absolute_uri(resume_path)

        dates_widget = {
            'course_date_blocks': [block for block in date_blocks if not isinstance(block, TodaysDate)],
            'dates_tab_link': dates_tab_link,
            'user_timezone': user_timezone,
        }

        # Only show the set course goal message for enrolled, unverified
        # users in a course that allows for verified statuses.
        is_already_verified = CourseEnrollment.is_enrolled_as_verified(request.user, course_key)
        if (not is_already_verified and
                has_course_goal_permission(request, course_key_string, {'is_enrolled': is_enrolled})):
            course_goals = {
                'goal_options': valid_course_goals_ordered(include_unsure=True),
                'selected_goal': None
            }

            selected_goal = get_course_goal(request.user, course_key)
            if selected_goal:
                course_goals['selected_goal'] = {
                    'key': selected_goal.goal_key,
                    'text': get_course_goal_text(selected_goal.goal_key),
                }
        else:
            course_goals = {
                'goal_options': [],
                'selected_goal': None
            }

        data = {
            'course_blocks': course_blocks,
            'course_expired_html': course_expired_html or None,
            'course_goals': course_goals,
            'course_tools': course_tools,
            'dates_widget': dates_widget,
            'enroll_alert': enroll_alert,
            'handouts_html': handouts_html or None,
            'has_ended': course.has_ended(),
            'offer_html': offer_html or None,
            'resume_course': resume_course,
            'welcome_message_html': welcome_message_html or None,
        }
        context = self.get_serializer_context()
        context['course_key'] = course_key
        context['enable_links'] = show_enrolled or allow_public
        serializer = self.get_serializer_class()(data, context=context)

        return Response(serializer.data)


@api_view(['POST'])
@authentication_classes((JwtAuthentication,))
@permission_classes((IsAuthenticated,))
def dismiss_welcome_message(request):
    course_id = request.data.get('course_id', None)

    # If body doesn't contain 'course_id', return 400 to client.
    if not course_id:
        raise ParseError(_("'course_id' is required."))

    # If body contains params other than 'course_id', return 400 to client.
    if len(request.data) > 1:
        raise ParseError(_("Only 'course_id' is expected."))

    try:
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        dismiss_current_update_for_user(request, course)
        return Response({'message': _('Welcome message successfully dismissed.')})
    except Exception:
        raise UnableToDismissWelcomeMessage


# Another version of this endpoint exists in ../course_goals/views.py
@api_view(['POST'])
@authentication_classes((JwtAuthentication, SessionAuthenticationAllowInactiveUser,))
@permission_classes((IsAuthenticated,))
def save_course_goal(request):
    course_id = request.data.get('course_id', None)
    goal_key = request.data.get('goal_key', None)

    # If body doesn't contain 'course_id', return 400 to client.
    if not course_id:
        raise ParseError(_("'course_id' is required."))

    # If body doesn't contain 'goal', return 400 to client.
    if not goal_key:
        raise ParseError(_("'goal_key' is required."))

    try:
        add_course_goal(request.user, course_id, goal_key)
        return Response({
            'header': _('Your course goal has been successfully set.'),
            'message': _('Course goal updated successfully.'),
        })
    except Exception:
        raise UnableToSaveCourseGoal
