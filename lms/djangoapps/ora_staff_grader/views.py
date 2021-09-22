"""
Views for Enhanced Staff Grader
"""
from lms.djangoapps.ora_staff_grader.serializers import CourseMetadataSerializer
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openedx.core.djangoapps.content.course_overviews.api import get_course_overview_or_none
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser


class InitializeView(RetrieveAPIView):
    """
    GET course metadata

    Response: {
        courseMetadata
        oraMetadata
        submissions
    }

    Returns:
        200
        400
        403
        404
        405
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        course_id = request.query_params['course_id']
        ora_location = request.query_params['ora_location']

        courseMetadata = get_course_overview_or_none(course_id)
        oraMetadata = self.get_ora_metadata(ora_location)
        submissionListData = []

        return Response({
            'courseMetadata': CourseMetadataSerializer(courseMetadata).data,
            'oraMetadata': oraMetadata,
            'submissions': submissionListData,
        })

    def get_ora_metadata(self, ora_location):
        return {}

    def get_submission_list(self, ora_location):
        return []