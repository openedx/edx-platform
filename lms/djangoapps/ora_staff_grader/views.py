"""
Views for Enhanced Staff Grader
"""
# NOTE: we intentionally do broad exception checking to return a clean error shape
# pylint: disable=broad-except

# NOTE: we intentionally add extra args using @require_params
# pylint: disable=arguments-differ

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import (
    SessionAuthenticationAllowInactiveUser,
)
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from lms.djangoapps.ora_staff_grader.constants import (
    PARAM_ORA_LOCATION,
    PARAM_SUBMISSION_ID,
)
from lms.djangoapps.ora_staff_grader.errors import (
    BadOraLocationResponse,
    GradeContestedResponse,
    InternalErrorResponse,
    LockContestedError,
    LockContestedResponse,
    UnknownErrorResponse,
    XBlockInternalError,
)
from lms.djangoapps.ora_staff_grader.ora_api import (
    check_submission_lock,
    claim_submission_lock,
    delete_submission_lock,
    get_assessment_info,
    get_submission_info,
    get_submissions,
    submit_grade,
)
from lms.djangoapps.ora_staff_grader.serializers import (
    InitializeSerializer,
    LockStatusSerializer,
    StaffAssessSerializer,
    SubmissionFetchSerializer,
    SubmissionStatusFetchSerializer,
)
from lms.djangoapps.ora_staff_grader.utils import require_params
from openedx.core.djangoapps.content.course_overviews.api import (
    get_course_overview_or_none,
)
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser


class StaffGraderBaseView(RetrieveAPIView):
    """
    Base view for common auth/permission setup used across ESG views.
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    permission_classes = (IsAuthenticated,)


class InitializeView(StaffGraderBaseView):
    """
    GET course metadata

    Response: {
        courseMetadata
        oraMetadata
        submissions
    }

    Errors:
    - MissingParamResponse (HTTP 400) for missing params
    - BadOraLocationResponse (HTTP 400) for bad ORA location
    - XBlockInternalError (HTTP 500) for an issue with ORA
    - UnknownError (HTTP 500) for other errors
    """

    @require_params([PARAM_ORA_LOCATION])
    def get(self, request, ora_location, *args, **kwargs):
        try:
            init_data = {}

            # Get ORA block and config (incl. rubric)
            ora_usage_key = UsageKey.from_string(ora_location)
            init_data["oraMetadata"] = modulestore().get_item(ora_usage_key)

            # Get course metadata
            course_id = str(ora_usage_key.course_key)
            init_data["courseMetadata"] = get_course_overview_or_none(course_id)

            # Get list of submissions for this ORA
            init_data["submissions"] = get_submissions(request, ora_location)

            return Response(InitializeSerializer(init_data).data)

        # Catch bad ORA location
        except (InvalidKeyError, ItemNotFoundError):
            return BadOraLocationResponse()

        # Issues with the XBlock handlers
        except XBlockInternalError as ex:
            return InternalErrorResponse(context=ex.context)

        # Blanket exception handling
        except Exception:
            return UnknownErrorResponse()


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
    - XBlockInternalError (HTTP 500) for an issue with ORA
    - UnknownError (HTTP 500) for other errors
    """

    @require_params([PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID])
    def get(self, request, ora_location, submission_uuid, *args, **kwargs):
        try:
            submission_info = get_submission_info(
                request, ora_location, submission_uuid
            )
            assessment_info = get_assessment_info(
                request, ora_location, submission_uuid
            )
            lock_info = check_submission_lock(request, ora_location, submission_uuid)

            serializer = SubmissionFetchSerializer(
                {
                    "submission_info": submission_info,
                    "assessment_info": assessment_info,
                    "lock_info": lock_info,
                }
            )

            return Response(serializer.data)

        # Issues with the XBlock handlers
        except XBlockInternalError as ex:
            return InternalErrorResponse(context=ex.context)

        # Blanket exception handling
        except Exception:
            return UnknownErrorResponse()


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
    - XBlockInternalError (HTTP 500) for an issue with ORA
    - UnknownError (HTTP 500) for other errors
    """

    @require_params([PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID])
    def get(self, request, ora_location, submission_uuid, *args, **kwargs):
        try:
            assessment_info = get_assessment_info(
                request, ora_location, submission_uuid
            )
            lock_info = check_submission_lock(request, ora_location, submission_uuid)

            serializer = SubmissionStatusFetchSerializer(
                {
                    "assessment_info": assessment_info,
                    "lock_info": lock_info,
                }
            )

            return Response(serializer.data)

        # Issues with the XBlock handlers
        except XBlockInternalError as ex:
            return InternalErrorResponse(context=ex.context)

        # Blanket exception handling
        except Exception:
            return UnknownErrorResponse()


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
    - XBlockInternalError (HTTP 500) for an issue with ORA
    - UnknownError (HTTP 500) for other errors
    """

    @require_params([PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID])
    def post(self, request, ora_location, submission_uuid, *args, **kwargs):
        """Update a grade"""
        try:
            # Reassert that we have ownership of the submission lock
            lock_info = check_submission_lock(request, ora_location, submission_uuid)
            if not lock_info.get("lock_status") == "in-progress":
                assessment_info = get_assessment_info(
                    request, ora_location, submission_uuid
                )
                submission_status = SubmissionStatusFetchSerializer(
                    {
                        "assessment_info": assessment_info,
                        "lock_info": lock_info,
                    }
                ).data
                return GradeContestedResponse(context=submission_status)

            # Transform grade data and submit assessment, rasies on failure
            context = {"submission_uuid": submission_uuid}
            grade_data = StaffAssessSerializer(request.data, context=context).data
            submit_grade(request, ora_location, grade_data)

            # Clear the lock on the graded submission
            delete_submission_lock(request, ora_location, submission_uuid)

            # Return submission status info to frontend
            assessment_info = get_assessment_info(
                request, ora_location, submission_uuid
            )
            lock_info = check_submission_lock(request, ora_location, submission_uuid)
            serializer = SubmissionStatusFetchSerializer(
                {
                    "assessment_info": assessment_info,
                    "lock_info": lock_info,
                }
            )
            return Response(serializer.data)

        # Issues with the XBlock handlers
        except XBlockInternalError as ex:
            return InternalErrorResponse(context=ex.context)

        # Blanket exception handling
        except Exception:
            return UnknownErrorResponse()


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
    - XBlockInternalError (HTTP 500) for an issue with ORA
    - UnknownError (HTTP 500) for other errors
    """

    @require_params([PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID])
    def post(self, request, ora_location, submission_uuid, *args, **kwargs):
        """Claim a submission lock"""
        try:
            # Validate ORA location
            UsageKey.from_string(ora_location)
            lock_info = claim_submission_lock(request, ora_location, submission_uuid)
            return Response(LockStatusSerializer(lock_info).data)

        # Catch bad ORA location
        except (InvalidKeyError, ItemNotFoundError):
            return BadOraLocationResponse()

        # Return updated lock info on error
        except LockContestedError:
            lock_info = check_submission_lock(request, ora_location, submission_uuid)
            lock_status = LockStatusSerializer(lock_info).data
            return LockContestedResponse(context=lock_status)

        # Issues with the XBlock handlers
        except XBlockInternalError as ex:
            return InternalErrorResponse(context=ex.context)

        # Blanket exception handling
        except Exception:
            return UnknownErrorResponse()

    @require_params([PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID])
    def delete(self, request, ora_location, submission_uuid, *args, **kwargs):
        """Clear a submission lock"""
        try:
            # Validate ORA location
            UsageKey.from_string(ora_location)
            lock_info = delete_submission_lock(request, ora_location, submission_uuid)
            return Response(LockStatusSerializer(lock_info).data)

        # Catch bad ORA location
        except (InvalidKeyError, ItemNotFoundError):
            return BadOraLocationResponse()

        # Return updated lock info on error
        except LockContestedError:
            lock_info = check_submission_lock(request, ora_location, submission_uuid)
            lock_status = LockStatusSerializer(lock_info).data
            return LockContestedResponse(context=lock_status)

        # Issues with the XBlock handlers
        except XBlockInternalError as ex:
            return InternalErrorResponse(context=ex.context)

        # Blanket exception handling
        except Exception:
            return UnknownErrorResponse()
