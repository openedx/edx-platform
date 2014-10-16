"""
The Enrollment API Views should be simple, lean HTTP endpoints for API access. This should
consist primarily of authentication, request validation, and serialization.

"""
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from enrollment import api


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def list_student_enrollments(self):
    return Response(api.get_enrollments(self.kwargs['username']))


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def get_course_enrollment(self):
    return Response(api.get_enrollment(self.kwargs['username'], self.kwargs['course_id']))


@api_view(['POST'])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def update_course_enrollment(self):
    if 'mode' in self.kwargs:
        return Response(api.update_enrollment(self.kwargs['username'], self.kwargs['course_id'], self.kwargs['mode']))
    elif 'deactivate' in self.kwargs:
        return Response(api.deactivate_enrollment(self.kwargs['username'], self.kwargs['course_id']))

