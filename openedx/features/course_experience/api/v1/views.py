from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException, ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openedx.core.djangoapps.schedules.utils import reset_self_paced_schedule


class UnableToResetDeadlines(APIException):
    status_code = 400
    default_detail = 'Unable to reset deadlines.'
    default_code = 'unable_to_reset_deadlines'


@permission_classes((IsAuthenticated,))
@api_view(['POST'])
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
