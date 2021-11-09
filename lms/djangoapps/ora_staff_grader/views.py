"""
Views for Enhanced Staff Grader
"""
from django.http.response import HttpResponseBadRequest, HttpResponseNotFound
from django.utils.translation import ugettext as _
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from lms.djangoapps.ora_staff_grader.serializers import InitializeSerializer, SubmissionDetailResponseSerializer
from lms.djangoapps.ora_staff_grader.utils import call_xblock_json_handler
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
        ora_location = request.query_params.get('ora_location')

        if not ora_location:
            return HttpResponseBadRequest(_("Query must contain an ora_location param."))

        response_data = {}

        # Get ORA block
        try:
            ora_usage_key = UsageKey.from_string(ora_location)
            response_data['oraMetadata'] = modulestore().get_item(ora_usage_key)
        except (InvalidKeyError, ItemNotFoundError):
            return HttpResponseNotFound(_("Invalid ora_location."))

        # Get course metadata
        course_id = str(ora_usage_key.course_key)
        response_data['courseMetadata'] = get_course_overview_or_none(course_id)

        # Get list of submissions for this ORA
        response_data['submissions'] = self.get_submissions(request, ora_location)

        # Get the rubric config for this ORA
        response_data['rubricConfig'] = self.get_rubric_config(request, ora_location)

        return Response(InitializeSerializer(response_data).data)

    def get_submissions(self, request, usage_id):
        """
        Get a list of submissions from the ORA's 'list_staff_workflows' XBlock.json_handler
        """
        return call_xblock_json_handler(request, usage_id, 'list_staff_workflows', {})

    def get_rubric_config(self, request, usage_id):
        """
        Get rubric data from the ORA's 'get_rubric' XBlock.json_handler
        """
        data = {
            'target_rubric_block_id': usage_id
        }
        return call_xblock_json_handler(request, usage_id, 'get_rubric', data)


class SubmissionFetchView(RetrieveAPIView):
    """
    GET submission contents and assessment info, if any

    Response: {

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
        ora_location = request.query_params.get('ora_location')
        if not ora_location:
            return HttpResponseBadRequest(_("Query must contain an ora_location param."))

        submission_uuid = request.query_params.get('submission_uuid')
        if not submission_uuid:
            return HttpResponseBadRequest(_("Query must contain a submission_uuid param."))

        submission_and_assessment_info = self.get_submission_and_assessment_info(ora_location, submission_uuid)
        return Response(SubmissionDetailResponseSerializer(submission_and_assessment_info).data)

    def get_submission_and_assessment_info(self, request, usage_id, submission_uuid):
        """
        Get submission content and assessment data from the ORA's 'get_submission_and_assessment_info' XBlock.json_handler
        """
        data = {
            'submission_uuid': submission_uuid
        }
        return call_xblock_json_handler(request, usage_id, 'get_submission_and_assessment_info', data)
