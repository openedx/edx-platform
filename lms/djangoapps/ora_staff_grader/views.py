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

        # Get list of submissions for this ORA
        submissions_metadata = self.get_submissions(request, ora_location)

        # Get the rubric config for this ORA
        rubric_config = self.get_rubric_config(request, ora_location)

        return Response({
            'courseMetadata': CourseMetadataSerializer(course_metadata).data,
            'oraMetadata': OpenResponseMetadataSerializer(openassessment_block).data,
            'submissions': {
                submission_id: SubmissionMetadataSerializer(submission).data
                for (submission_id, submission) in submissions_metadata.items()
            },
            'rubricConfig': rubric_config,
        })

    def get_submissions(self, request, usage_id):
        """
        Get a list of submissions from the ORA's 'list_staff_workflows' XBlock.json_handler
        """
        return self._call_xblock_json_handler(request, usage_id, 'list_staff_workflows')

    def get_rubric_config(self, request, usage_id):
        """
        Get rubric data from the ORA's 'get_rubric' XBlock.json_handler
        """
        data = {
            'target_rubric_block_id': usage_id
        }
        return self._call_xblock_json_handler(request, usage_id, 'get_rubric', data)

    def _call_xblock_json_handler(self, request, usage_id, handler_name, data={}):
        """
        Create an internally-routed XBlock.json_handler request.
        The internal auth code/param unpacking requires a POST request with payload in the body.

        params:
            request (HttpRequest): Originating web request, we're going to borrow auth headers/cookies from this
            usage_id (str): Usage ID of the XBlock for running the handler
            handler_name (str): the name of the XBlock handler method
            data (dict): Data to be encoded and sent as the body of the POST request
        """
        # XBlock.json_handler operates through a POST request
        proxy_request = clone_request(request, "POST")
        proxy_request.META["REQUEST_METHOD"] = "POST"

        # The body is an encoded JSON blob
        proxy_request.body = json.dumps(data).encode()

        # Course ID can be retrieved from the usage_id
        usage_key = UsageKey.from_string(usage_id)
        course_id = str(usage_key.course_key)

        # Send and decode the request
        response = handle_xblock_callback(proxy_request, course_id, usage_id, handler_name)
        return json.loads(response.content)
