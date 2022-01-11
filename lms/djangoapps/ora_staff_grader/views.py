"""
Views for Enhanced Staff Grader
"""
import json
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from lms.djangoapps.ora_staff_grader.constants import PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID
from lms.djangoapps.ora_staff_grader.errors import (
    BadOraLocationResponse,
    ExceptionWithContext,
    GradeContestedResponse,
    LockContestedError,
    SubmitGradeErrorResponse,
    LockContestedResponse,
    UnknownErrorResponse,
)
from lms.djangoapps.ora_staff_grader.serializers import (
    InitializeSerializer,
    LockStatusSerializer,
    StaffAssessSerializer,
    SubmissionFetchSerializer,
    SubmissionStatusFetchSerializer,
)
from lms.djangoapps.ora_staff_grader.utils import call_xblock_json_handler, require_params
from openedx.core.djangoapps.content.course_overviews.api import get_course_overview_or_none
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser


class StaffGraderBaseView(RetrieveAPIView):
    """
    Base view for common auth/permission setup and XBlock handlers used across ESG views.

    All XBlock handlers are wrapped to either return data or raise an exception to make error-handling clear.
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    permission_classes = (IsAuthenticated,)

    def get_submissions(self, request, usage_id):
        """
        Get a list of submissions from the ORA's 'list_staff_workflows' XBlock.json_handler
        """
        response = call_xblock_json_handler(request, usage_id, 'list_staff_workflows', {})

        if response.status_code != 200:
            raise Exception()

        return json.loads(response.content)

    def get_rubric_config(self, request, usage_id):
        """
        Get rubric data from the ORA's 'get_rubric' XBlock.json_handler
        """
        data = {'target_rubric_block_id': usage_id}
        response = call_xblock_json_handler(request, usage_id, 'get_rubric', data)

        # Unhandled errors might not be JSON, catch before loading
        if response.status_code != 200:
            raise Exception()

        response_data = json.loads(response.content)

        # Handled faillure still returns HTTP 200 but with 'success': False and supplied error message "msg"
        if not response_data.get('success', False):
            raise ExceptionWithContext(context={"msg": response_data.get('msg', '')})

        return response_data['rubric']

    def get_submission_info(self, request, usage_id, submission_uuid):
        """
        Get submission content from ORA 'get_submission_info' XBlock.json_handler
        """
        data = {'submission_uuid': submission_uuid}
        response = call_xblock_json_handler(request, usage_id, 'get_submission_info', data)

        if response.status_code != 200:
            raise Exception()

        return json.loads(response.content)

    def get_assessment_info(self, request, usage_id, submission_uuid):
        """
        Get assessment data from ORA 'get_assessment_info' XBlock.json_handler
        """
        data = {'submission_uuid': submission_uuid}
        response = call_xblock_json_handler(request, usage_id, 'get_assessment_info', data)

        if response.status_code != 200:
            raise Exception()

        return json.loads(response.content)

    def submit_grade(self, request, usage_id, grade_data):
        """
        Submit a grade for an assessment.

        Returns: {'success': True/False, 'msg': err_msg}
        """
        response = call_xblock_json_handler(request, usage_id, 'staff_assess', grade_data)

        # Unhandled errors might not be JSON, catch before loading
        if response.status_code != 200:
            raise Exception()

        response_data = json.loads(response.content)

        # Handled faillure still returns HTTP 200 but with 'success': False and supplied error message "msg"
        if not response_data.get('success', False):
            raise ExceptionWithContext(context={"msg": response_data.get('msg', '')})

        return response_data

    def check_submission_lock(self, request, usage_id, submission_uuid):
        """
        Look up lock info for the given submission by calling the ORA's 'check_submission_lock' XBlock.json_handler
        """
        data = {'submission_uuid': submission_uuid}
        response = call_xblock_json_handler(request, usage_id, 'check_submission_lock', data)

        # Unclear that there would every be an error (except network/auth) but good to catch here
        if response.status_code != 200:
            raise Exception()

        return json.loads(response.content)

    def claim_submission_lock(self, request, usage_id, submission_uuid):
        """
        Attempt to claim a submission lock for grading.

        Returns:
        - lockStatus (string) - One of ['not-locked', 'locked', 'in-progress']
        """
        body = {"submission_uuid": submission_uuid}
        response = call_xblock_json_handler(request, usage_id, 'claim_submission_lock', body)

        # Lock contested returns a 403
        if response.status_code == 403:
            raise LockContestedError()

        # Other errors should raise a blanket exception
        elif response.status_code != 200:
            raise Exception()

        return json.loads(response.content)

    def delete_submission_lock(self, request, usage_id, submission_uuid):
        """
        Attempt to claim a submission lock for grading.

        Returns:
        - lockStatus (string) - One of ['not-locked', 'locked', 'in-progress']
        """
        body = {"submission_uuid": submission_uuid}

        # Return raw response to preserve HTTP status codes for failure states
        response = call_xblock_json_handler(request, usage_id, 'delete_submission_lock', body)

        # Lock contested returns a 403
        if response.status_code == 403:
            raise LockContestedError()

        # Other errors should raise a blanket exception
        elif response.status_code != 200:
            raise Exception()

        return json.loads(response.content)


class InitializeView(StaffGraderBaseView):
    """
    GET course metadata

    Response: {
        courseMetadata
        oraMetadata
        submissions
        rubricConfig
    }

    Errors:
    - MissingParamResponse (HTTP 400) for missing params
    - BadOraLocationResponse (HTTP 400) for bad ORA location
    """
    @require_params([PARAM_ORA_LOCATION])
    def get(self, request, ora_location, *args, **kwargs):
        response_data = {}

        # Get ORA block
        try:
            ora_usage_key = UsageKey.from_string(ora_location)
            response_data['oraMetadata'] = modulestore().get_item(ora_usage_key)
        except (InvalidKeyError, ItemNotFoundError):
            return BadOraLocationResponse()

        # Get course metadata
        course_id = str(ora_usage_key.course_key)
        response_data['courseMetadata'] = get_course_overview_or_none(course_id)

        # Get list of submissions for this ORA
        response_data['submissions'] = self.get_submissions(request, ora_location)

        # Get the rubric config for this ORA
        response_data['rubricConfig'] = self.get_rubric_config(request, ora_location)

        return Response(InitializeSerializer(response_data).data)


class SubmissionFetchView(StaffGraderBaseView):
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

    Errors:
    - MissingParamResponse (HTTP 400) for missing params
    """
    @require_params([PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID])
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


class SubmissionStatusFetchView(StaffGraderBaseView):
    """
    GET submission grade status, lock status, and grade data

    Response: {
        gradeStatus: (str) one of [graded, ungraded]
        lockStatus: (str) one of [locked, unlocked, in-progress]
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
    }

    Errors:
    - MissingParamResponse (HTTP 400) for missing params
    """
    @require_params([PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID])
    def get(self, request, ora_location, submission_uuid, *args, **kwargs):
        assessment_info = self.get_assessment_info(request, ora_location, submission_uuid)
        lock_info = self.check_submission_lock(request, ora_location, submission_uuid)

        serializer = SubmissionStatusFetchSerializer({
            'assessment_info': assessment_info,
            'lock_info': lock_info,
        })

        return Response(serializer.data)


class UpdateGradeView(StaffGraderBaseView):
    """
    POST submit a grade for a submission

    Body: {
        overallFeedback: (string) overall feedback
        criteria: [
            {
                name: (string) name of criterion
                feedback: (string, optional) feedback for criterion
                selectedOption: (string) name of selected option or None if feedback-only criterion
            },
            ... (one per criteria)
        ]
    }

    Response: {
        gradeStatus: (string) - One of ['graded', 'ungraded']
        lockStatus: (string) - One of ['unlocked', 'locked', 'in-progress']
        gradeData: {
            score: (dict or None) {
                pointsEarned: (int) earned points
                pointsPossible: (int) possible points
            }
            overallFeedback: (string) overall feedback
            criteria: (list of dict) [{
                name: (str) name of criterion
                feedback: (str) feedback for criterion
                selectedOption: (str) name of selected option or None if feedback-only criterion
            }]
        }
    }

    Errors:
    - MissingParamResponse (HTTP 400) for missing params
    - GradeContestedResponse (HTTP 409) for trying to submit a grade for a submission you don't have an active lock for
    - SubmitGradeErrorResponse (HTTP 500) for ORA failures to submit a grade
    """
    @require_params([PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID])
    def post(self, request, ora_location, submission_uuid, *args, **kwargs):
        # Reassert that we have ownership of the submission lock
        lock_info = self.check_submission_lock(request, ora_location, submission_uuid)
        if not lock_info.get('lock_status') == 'in-progress':
            assessment_info = self.get_assessment_info(request, ora_location, submission_uuid)
            submission_status = SubmissionStatusFetchSerializer({
                'assessment_info': assessment_info,
                'lock_info': lock_info,
            }).data

            return GradeContestedResponse(context=submission_status)

        # Transform data from frontend format to staff assess format
        context = {'submission_uuid': submission_uuid}
        grade_data = StaffAssessSerializer(request.data, context=context).data

        # Perform the staff assessment
        response = self.submit_grade(request, ora_location, grade_data)

        # Failed response returns 'success': False with an error message
        if not response['success']:
            return SubmitGradeErrorResponse(context={"msg": response['msg']})

        # Remove the lock on the graded submission
        self.delete_submission_lock(request, ora_location, submission_uuid)

        # Return submission status info to frontend
        assessment_info = self.get_assessment_info(request, ora_location, submission_uuid)
        lock_info = self.check_submission_lock(request, ora_location, submission_uuid)

        serializer = SubmissionStatusFetchSerializer({
            'assessment_info': assessment_info,
            'lock_info': lock_info,
        })

        return Response(serializer.data)


class SubmissionLockView(StaffGraderBaseView):
    """
    POST claim a submission lock for grading
    DELETE release a submission lock

    Params:
    - ora_location (str/UsageID): ORA location for XBlock handling
    - submissionUUID (UUID): A submission to lock/unlock

    Response: {
        lockStatus
    }

    Errors:
    - MissingParamResponse (HTTP 400) for missing params
    - LockContestedResponse (HTTP 409) for contested lock
    """
    @require_params([PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID])
    def post(self, request, ora_location, submission_uuid, *args, **kwargs):
        """ Claim a submission lock """
        try:
            # Validate ORA location
            UsageKey.from_string(ora_location)
            lock_info = self.claim_submission_lock(request, ora_location, submission_uuid)
            return Response(LockStatusSerializer(lock_info).data)

        # Catch bad ORA location
        except (InvalidKeyError, ItemNotFoundError):
            return BadOraLocationResponse()

        # Return updated lock info on error
        except LockContestedError:
            lock_info = self.check_submission_lock(request, ora_location, submission_uuid)
            lock_status = LockStatusSerializer(lock_info).data
            return LockContestedResponse(context=lock_status)

        # Blanket exception handling
        except Exception:
            return UnknownErrorResponse()

    @require_params([PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID])
    def delete(self, request, ora_location, submission_uuid, *args, **kwargs):
        """ Clear a submission lock """
        try:
            # Validate ORA location
            UsageKey.from_string(ora_location)
            lock_info = self.delete_submission_lock(request, ora_location, submission_uuid)
            return Response(LockStatusSerializer(lock_info).data)

        # Catch bad ORA location
        except (InvalidKeyError, ItemNotFoundError):
            return BadOraLocationResponse()

        # Return updated lock info on error
        except LockContestedError:
            lock_info = self.check_submission_lock(request, ora_location, submission_uuid)
            lock_status = LockStatusSerializer(lock_info).data
            return LockContestedResponse(context=lock_status)

        # Blanket exception handling
        except Exception:
            return UnknownErrorResponse()
