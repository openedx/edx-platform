"""
The Enrollment API Views should be simple, lean HTTP endpoints for API access. This should
consist primarily of authentication, request validation, and serialization.

"""
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from enrollment import api


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def list_student_enrollments(request):
    return Response(api.get_enrollments(request.user.username))


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def get_course_enrollment(request, course_id=None):
    return Response(api.get_enrollment(request.user.username, course_id))


@api_view(['POST'])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def update_course_enrollment(request, course_id=None, mode=None, deactivate=False):
    from nose.tools import set_trace; set_trace()
    if mode:
        return Response(api.update_enrollment(request.user.username, course_id, mode))
    elif deactivate:
        return Response(api.deactivate_enrollment(request.user.username, course_id))
    elif course_id:
        return Response(api.add_enrollment(request.user.username, course_id))

