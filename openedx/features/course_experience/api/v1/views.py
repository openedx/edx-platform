from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import APIException, ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser

from openedx.core.djangoapps.schedules.utils import reset_self_paced_schedule
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser


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
    course_key = request.data.get('course_key', None)

    # If body doesnt contain 'course_key', return 400 to client.
    if not course_key:
        raise ParseError("'course_key' is required.")

    # If body contains params other than 'course_key', return 400 to client.
    if len(request.data) > 1:
        raise ParseError("Only 'course_key' is expected.")

    try:
        reset_self_paced_schedule(request.user, course_key)
        return Response({'message': 'Deadlines successfully reset.'})
    except Exception:
        raise UnableToResetDeadlines
