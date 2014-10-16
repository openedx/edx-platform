"""
The Enrollment API Views should be simple, lean HTTP endpoints for API access. This should
consist primarily of authentication, request validation, and serialization.

"""
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from enrollment import api


class EnrollmentUserThrottle(UserRateThrottle):
        rate = '50/second'  # TODO Limit significantly after performance testing.


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
@throttle_classes([EnrollmentUserThrottle])
def list_student_enrollments(request):
    return Response(api.get_enrollments(request.user.username))


@api_view(['GET', 'POST'])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
@throttle_classes([EnrollmentUserThrottle])
def get_course_enrollment(request, course_id=None):
    if 'mode' in request.DATA:
        return Response(api.update_enrollment(request.user.username, course_id, request.DATA['mode']))
    elif 'deactivate' in request.DATA:
        return Response(api.deactivate_enrollment(request.user.username, course_id))
    elif course_id and request.method == 'POST':
        return Response(api.add_enrollment(request.user.username, course_id))
    else:
        return Response(api.get_enrollment(request.user.username, course_id))
