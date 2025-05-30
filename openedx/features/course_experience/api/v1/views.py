"""
Views for Course Experience API.
"""
import logging

from django.utils.html import format_html
from django.utils.translation import gettext as _

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import APIException, ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.course_goals.models import UserActivity
from lms.djangoapps.courseware.courses import get_course_with_access

from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.features.course_experience.api.v1.serializers import CourseDeadlinesMobileSerializer
from openedx.features.course_experience.url_helpers import get_learning_mfe_home_url
from openedx.features.course_experience.api.v1.utils import reset_deadlines_for_course

log = logging.getLogger(__name__)


class UnableToResetDeadlines(APIException):
    status_code = 400
    default_detail = 'Unable to reset deadlines.'
    default_code = 'unable_to_reset_deadlines'


@api_view(['POST'])
@authentication_classes((
    JwtAuthentication, BearerAuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser,
))
@permission_classes((IsAuthenticated,))
def reset_course_deadlines(request):
    """
    Set the start_date of a schedule to today, which in turn will adjust due dates for
    sequentials belonging to a self paced course

    Request Parameters:
        course_key: course key
        research_event_data: any data that should be included in the research tracking event
            Example: sending the location of where the reset deadlines banner (i.e. outline-tab)

    IMPORTANT NOTE: If updates are happening to the logic here, ALSO UPDATE the `reset_course_deadlines`
    function in common/djangoapps/util/views.py as well.
    """
    course_key = request.data.get('course_key', None)
    research_event_data = request.data.get('research_event_data', {})

    # If body doesnt contain 'course_key', return 400 to client.
    if not course_key:
        raise ParseError(_("'course_key' is required."))

    try:
        reset_deadlines_for_course(request, course_key, research_event_data)

        body_link = get_learning_mfe_home_url(course_key=course_key, url_fragment='dates')

        return Response({
            'body': format_html('<a href="{}">{}</a>', body_link, _('View all dates')),
            'header': _('Your due dates have been successfully shifted to help you stay on track.'),
            'link': body_link,
            'link_text': _('View all dates'),
            'message': _('Deadlines successfully reset.'),
        })
    except Exception as reset_deadlines_exception:
        log.exception('Error occurred while trying to reset deadlines!')
        raise UnableToResetDeadlines from reset_deadlines_exception


@api_view(['POST'])
@authentication_classes((
    JwtAuthentication, BearerAuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser,
))
@permission_classes((IsAuthenticated,))
def reset_multiple_course_deadlines(request):
    """
    Set the start_date of a schedule to today for multiple courses

    Request Parameters:
        course_keys: list of course keys
        research_event_data: any data that should be included in the research tracking event
            Example: sending the location of where the reset deadlines banner (i.e. outline-tab)

    Returns:
        success_course_keys: list of course keys for which deadlines were successfully reset
        failed_course_keys: list of course keys for which deadlines could not be reset
    """
    course_keys = request.data.get('course_keys', [])
    research_event_data = request.data.get('research_event_data', {})

    if not course_keys:
        raise ParseError(_("'course_keys' is required."))

    failed_course_keys = []
    succes_course_keys = []

    for course_key in course_keys:
        try:
            reset_deadlines_for_course(request, course_key, research_event_data)
            succes_course_keys.append(course_key)
        except Exception:  # pylint: disable=broad-exception-caught
            log.exception(f'Error occurred while trying to reset deadlines for course {course_key}!')
            failed_course_keys.append(course_key)
            continue

    return Response({
        "success_course_keys": succes_course_keys,
        "failed_course_keys": failed_course_keys,
    })


class CourseDeadlinesMobileView(RetrieveAPIView):
    """
    **Use Cases**

        Request course deadline info for mobile

    **Example Requests**

        GET api/course_experience/v1/course_deadlines_info/{course_key}

    **Response Values**

        Body consists of the following fields:

        dates_banner_info: (obj)
            missed_deadlines: (bool) Whether the user has missed any graded content deadlines for the given course.
            missed_gated_content: (bool) Whether the user has missed any gated content for the given course.
            content_type_gating_enabled: (bool) Whether content type gating is enabled for this enrollment.
            verified_upgrade_link: (str) The URL to ecommerce IDA for purchasing the verified upgrade.

    **Returns**

        * 200 on success with above fields.
        * 401 if the user is not authenticated.
        * 404 if the course is not available or cannot be seen.
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)
    serializer_class = CourseDeadlinesMobileSerializer

    def get(self, request, *args, **kwargs):
        course_key_string = kwargs.get('course_key_string')
        course_key = CourseKey.from_string(course_key_string)
        # Although this course data is not used this method will return 404 if course does not exist
        get_course_with_access(request.user, 'load', course_key)

        # Record user activity for tracking progress towards a user's course goals (for mobile app)
        UserActivity.record_user_activity(
            request.user, course_key, request=request, only_if_mobile_app=True
        )

        serializer = self.get_serializer({})
        return Response(serializer.data)
