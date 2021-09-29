"""
Views for Enhanced Staff Grader
"""
import json

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import UsageKey
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import clone_request
from xmodule.modulestore.django import modulestore

from lms.djangoapps.courseware.module_render import handle_xblock_callback
from lms.djangoapps.ora_staff_grader.serializers import (
    CourseMetadataSerializer,
    OpenResponseMetadataSerializer,
    SubmissionMetadataSerializer
)
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

    def get(self, request, *args, **kwargs):
        ora_location = request.query_params['ora_location']

        # Get ORA block
        ora_usage_key = UsageKey.from_string(ora_location)
        openassessment_block = modulestore().get_item(ora_usage_key)

        # Get course metadata
        course_id = str(ora_usage_key.course_key)
        course_metadata = get_course_overview_or_none(course_id)

        # Get list of submissions for the ORA
        submissions_metadata = self.get_submissions(request, course_id, ora_location)

        return Response({
            'courseMetadata': CourseMetadataSerializer(course_metadata).data,
            'oraMetadata': OpenResponseMetadataSerializer(openassessment_block).data,
            'submissions': {
                submission_id: SubmissionMetadataSerializer(submission).data
                for (submission_id, submission) in submissions_metadata.items()
            },
        })

    def get_submissions(self, request, course_id, usage_id):
        """
        Create an XBlock handler request (routed internally) to get a list of submissions (staff workflows)
        """
        # Normally an XBlock.json_handler is routed through a POST request.
        # We have to pass along a fake POST request to work with the handler auth/routing tooling.
        proxy_request = clone_request(request, "POST")
        proxy_request.META["REQUEST_METHOD"] = "POST"

        # Here is where we'd set the body, but it's empty for our use case.
        proxy_request.body = b'{}'

        # Send and decode the request
        response = handle_xblock_callback(proxy_request, course_id, usage_id, 'list_staff_workflows')
        return json.loads(response.content)
