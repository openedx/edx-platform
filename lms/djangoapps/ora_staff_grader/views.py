"""
Views for Enhanced Staff Grader
"""
from lms.djangoapps.ora_staff_grader.serializers import CourseMetadataSerializer, OpenResponseMetadataSerializer
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import UsageKey
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from xmodule.modulestore.django import modulestore

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

        # Get course metadata
        course_metadata = get_course_overview_or_none(course_id)

        # Get ORA block
        ora_usage_key = UsageKey.from_string(ora_location)
        openassessment_block = modulestore().get_item(ora_usage_key)

        # TODO - Get submission list
        submisison_list_data = self.get_submission_list(ora_location)

        return Response({
            'courseMetadata': CourseMetadataSerializer(course_metadata).data,
            'oraMetadata': OpenResponseMetadataSerializer(openassessment_block).data,
            'submissions': submisison_list_data,
        })

    def get_submission_list(self, ora_location):
        return []