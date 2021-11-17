"""
Views for Enhanced Staff Grader
"""
import json
from django.http.response import HttpResponseBadRequest
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

from lms.djangoapps.ora_staff_grader.errors import ERR_BAD_ORA_LOCATION
from lms.djangoapps.ora_staff_grader.serializers import InitializeSerializer, LockStatusSerializer, SubmissionFetchSerializer
from lms.djangoapps.ora_staff_grader.utils import call_xblock_json_handler, require_params
from openedx.core.djangoapps.content.course_overviews.api import get_course_overview_or_none
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser


class InitializeView(RetrieveAPIView):
    """
    GET course metadata

    Response: {
        courseMetadata
        oraMetadata
        submissions
        rubricConfig
    }

    Returns:
    - 200 on success
    - 400 for invalid/missing ora_location
    - 403 for invalid access/credentials
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)

    @require_params(['ora_location'])
    def get(self, request, ora_location, *args, **kwargs):
        response_data = {}

        # Get ORA block
        try:
            ora_usage_key = UsageKey.from_string(ora_location)
            response_data['oraMetadata'] = modulestore().get_item(ora_usage_key)
        except (InvalidKeyError, ItemNotFoundError):
            return HttpResponseBadRequest(ERR_BAD_ORA_LOCATION)

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
        gradeData: {
            score: (dict or None) {
                pointsEarned: (int) earned points
                pointsPossible: (int) possible points
            }
            overallFeedback: (string) overall feedback
            criteria: (list of dict) [{
                name: (str) name of criterion
                feedback: (str) feedback for criterion
                points: (int) points of selected option or None if feedback-only criterion
                selectedOption: (str) name of selected option or None if feedback-only criterion
            }]
        }
        response: {
            text: (list of string), [the html content of text responses]
            files: (list of dict) [{
                downloadUrl: (string) file download url
                description: (string) file description
                name: (string) filename
            }]
        }
    }
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)

    @require_params(['ora_location', 'submission_uuid'])
    def get(self, request, ora_location, submission_uuid, *args, **kwargs):
        submission_info = self.get_submission_info(request, ora_location, submission_uuid)
        assessment_info = self.get_assessment_info(request, ora_location, submission_uuid)
        lock_info = self.check_submission_lock(request, ora_location, submission_uuid)

        serializer = SubmissionFetchSerializer({
            'submission_info': submission_info,
            'assessment_info': assessment_info,
            'lock_info': lock_info,
        })

        return Response(serializer.data)

    def get_submission_info(self, request, usage_id, submission_uuid):
        """
        Get submission content from ORA 'get_submission_info' XBlock.json_handler
        """
        data = {
            'submission_uuid': submission_uuid
        }
        return call_xblock_json_handler(request, usage_id, 'get_submission_info', data)

    def get_assessment_info(self, request, usage_id, submission_uuid):
        """
        Get assessment data from ORA 'get_assessment_info' XBlock.json_handler
        """
        data = {
            'submission_uuid': submission_uuid
        }
        return call_xblock_json_handler(request, usage_id, 'get_assessment_info', data)

    def check_submission_lock(self, request, usage_id, submission_uuid):
        """
        Look up lock info for the given submission by calling the ORA's 'check_submission_lock' XBlock.json_handler
        """
        data = {
            'submission_uuid': submission_uuid
        }
        return call_xblock_json_handler(request, usage_id, 'check_submission_lock', data)


class SubmissionLockView(RetrieveAPIView):
    """
    POST claim a submission lock for grading
    DELETE release a submission lock

    Params:
    - ora_location (str/UsageID): ORA location for XBlock handling
    - submissionUUID (UUID): A submission to lock/unlock

    Response: {
        lockStatus
    }

    Raises:
    - 400 for bad request or missing query params
    - 403 for bad auth or contested lock with payload { 'error': '<error-code>'}
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)

    @require_params(['ora_location', 'submissionId'])
    def post(self, request, ora_location, submission_uuid, *args, **kwargs):
        """ Claim a submission lock """
        # Validate ORA location
        try:
            UsageKey.from_string(ora_location)
        except (InvalidKeyError, ItemNotFoundError):
            return HttpResponseBadRequest(ERR_BAD_ORA_LOCATION)

        response = self.claim_submission_lock(request, ora_location, submission_uuid)

        # In the case of an error, pass through the error response code directly
        if response.status_code != 200:
            return response

        # Success should return serialized lock info
        response_data = json.loads(response.content)
        return Response(LockStatusSerializer(response_data).data)

    @require_params(['ora_location', 'submissionId'])
    def delete(self, request, ora_location, submission_uuid, *args, **kwargs):
        """ Clear a submission lock """
        # Validate ORA location
        try:
            UsageKey.from_string(ora_location)
        except (InvalidKeyError, ItemNotFoundError):
            return HttpResponseBadRequest(ERR_BAD_ORA_LOCATION)

        response = self.delete_submission_lock(request, ora_location, submission_uuid)

        # In the case of an error, pass through the error response code directly
        if response.status_code != 200:
            return response

        # Success should return serialized lock info
        response_data = json.loads(response.content)
        return Response(LockStatusSerializer(response_data).data)

    def claim_submission_lock(self, request, usage_id, submission_uuid):
        """
        Attempt to claim a submission lock for grading.

        Returns:
        - lockStatus (string) - One of ['not-locked', 'locked', 'in-progress']
        """
        body = {
            "submission_id": submission_uuid
        }

        # running with decode=False to preserve HTTP status codes for failure states
        return call_xblock_json_handler(request, usage_id, 'claim_submission_lock', body, decode=False)

    def delete_submission_lock(self, request, usage_id, submission_uuid):
        """
        Attempt to claim a submission lock for grading.

        Returns:
        - lockStatus (string) - One of ['not-locked', 'locked', 'in-progress']
        """
        body = {
            "submission_id": submission_uuid
        }

        # running with decode=False to preserve HTTP status codes for failure states
        return call_xblock_json_handler(request, usage_id, 'delete_submission_lock', body, decode=False)
