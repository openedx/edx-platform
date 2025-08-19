"""
Utility functions for student enrollment operations.

This module contains reusable functions for processing student enrollments
that can be used in both synchronous and asynchronous contexts.
"""

import logging
from typing import Callable, Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.models import (
    ALLOWEDTOENROLL_TO_ENROLLED,
    ALLOWEDTOENROLL_TO_UNENROLLED,
    DEFAULT_TRANSITION_STATE,
    ENROLLED_TO_ENROLLED,
    ENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ALLOWEDTOENROLL,
    UNENROLLED_TO_ENROLLED,
    UNENROLLED_TO_UNENROLLED,
    CourseEnrollment,
    ManualEnrollmentAudit,
)
from lms.djangoapps.instructor.enrollment import (
    enroll_email,
    get_email_params,
    get_user_email_language,
    unenroll_email,
)
from lms.djangoapps.instructor.views.tools import get_student_from_identifier
from openedx.core.lib.courses import get_course_by_id

log = logging.getLogger(__name__)


User = get_user_model()


def process_single_student_enrollment(
    request_user,
    course_key: CourseKey,
    action: str,
    identifier: str,
    auto_enroll: bool,
    email_students: bool,
    reason: str | None,
    email_params: dict | None,
):
    """
    Process enrollment/unenrollment for a single student.

    Args:
        request_user (User): User who initiated the enrollment operation
        course_key (CourseKey): CourseKey object for the course
        action (str): 'enroll' or 'unenroll'
        identifier (str): Student identifier (email or username)
        auto_enroll (bool): Whether to auto-enroll in verified track if applicable
        email_students (bool): Whether to send enrollment emails
        reason (str | None): Optional reason for enrollment change
        email_params (dict | None): Pre-computed email parameters (optional)

    Returns:
        dict: Result of the enrollment operation with keys:
            - identifier: The student identifier
            - success: Boolean indicating if operation was successful
            - before: State before operation (if successful)
            - after: State after operation (if successful)
            - error_type: Type of error ('invalid_identifier', 'validation_error', 'general_error')
            - error_message: Error message (if failed)
    """
    enrollment_obj = None
    state_transition = DEFAULT_TRANSITION_STATE
    identified_user = None
    email = None
    language = None

    try:
        identified_user = get_student_from_identifier(identifier)
    except User.DoesNotExist:
        email = identifier
    else:
        email = identified_user.email
        language = get_user_email_language(identified_user)

    try:
        validate_email(email)  # Raises ValidationError if invalid

        if action == "enroll":
            before, after, enrollment_obj = enroll_email(
                course_key, email, auto_enroll, email_students, {**email_params}, language=language
            )
            before_enrollment = before.to_dict()["enrollment"]
            before_user_registered = before.to_dict()["user"]
            before_allowed = before.to_dict()["allowed"]
            after_enrollment = after.to_dict()["enrollment"]
            after_allowed = after.to_dict()["allowed"]

            if before_user_registered:
                if after_enrollment:
                    if before_enrollment:
                        state_transition = ENROLLED_TO_ENROLLED
                    elif before_allowed:
                        state_transition = ALLOWEDTOENROLL_TO_ENROLLED
                    else:
                        state_transition = UNENROLLED_TO_ENROLLED
            elif after_allowed:
                state_transition = UNENROLLED_TO_ALLOWEDTOENROLL

        elif action == "unenroll":
            before, after = unenroll_email(course_key, email, email_students, {**email_params}, language=language)
            before_enrollment = before.to_dict()["enrollment"]
            before_allowed = before.to_dict()["allowed"]
            enrollment_obj = CourseEnrollment.get_enrollment(identified_user, course_key) if identified_user else None

            if before_enrollment:
                state_transition = ENROLLED_TO_UNENROLLED
            elif before_allowed:
                state_transition = ALLOWEDTOENROLL_TO_UNENROLLED
            else:
                state_transition = UNENROLLED_TO_UNENROLLED

        # Create audit record
        ManualEnrollmentAudit.create_manual_enrollment_audit(
            request_user, email, state_transition, reason, enrollment_obj
        )

        return {
            "identifier": identifier,
            "before": before.to_dict(),
            "after": after.to_dict(),
            "success": True,
            "state_transition": state_transition,
        }
    except ValidationError:
        return {
            "identifier": identifier,
            "invalidIdentifier": True,
            "success": False,
            "error_type": "invalid_identifier",
            "error_message": "Invalid email address",
        }
    except Exception as exc:  # pylint: disable=broad-exception-caught
        log.exception("Error while processing student")
        log.exception(exc)
        return {
            "identifier": identifier,
            "error": True,
            "success": False,
            "error_type": "general_error",
            "error_message": str(exc),
        }


def process_student_enrollment_batch(
    request_user,
    course_key: CourseKey,
    action: str,
    identifiers: list[str],
    auto_enroll: bool,
    email_students: bool,
    reason: str | None,
    secure: bool,
    progress_callback: Optional[Callable] = None,
):
    """
    Process a batch of student enrollment/unenrollment operations.

    Args:
        request_user (User): User who initiated the batch operation
        course_key (CourseKey): CourseKey object for the course
        action (str): 'enroll' or 'unenroll'
        identifiers (list[str]): List of student identifiers (emails or usernames)
        auto_enroll (bool): Whether to auto-enroll in verified track if applicable
        email_students (bool): Whether to send enrollment emails
        reason (str | None): Optional reason for enrollment change
        secure (bool): Whether the request is secure (HTTPS)
        progress_callback (Optional[Callable]): Optional callback function to report progress
            Should accept (current, total, results) parameters

    Returns:
        dict: Batch processing results with keys:
            - action: The action performed
            - auto_enroll: Auto-enrollment setting
            - results: List of individual enrollment results
            - successful_operations: Count of successful operations
            - failed_operations: Count of failed operations
            - total_students: Total number of students processed
    """
    email_params = {}
    if email_students:
        course = get_course_by_id(course_key)
        email_params = get_email_params(course, auto_enroll, secure=secure)

    results = []
    successful_operations = 0
    failed_operations = 0
    total_students = len(identifiers)

    for i, identifier in enumerate(identifiers):
        result = process_single_student_enrollment(
            request_user=request_user,
            course_key=course_key,
            action=action,
            identifier=identifier,
            auto_enroll=auto_enroll,
            email_students=email_students,
            reason=reason,
            email_params=email_params,
        )

        results.append(result)

        if result["success"]:
            successful_operations += 1
        else:
            failed_operations += 1

        if progress_callback:
            progress_callback(i + 1, total_students, results)

    return {
        "action": action,
        "auto_enroll": auto_enroll,
        "results": results,
        "successful_operations": successful_operations,
        "failed_operations": failed_operations,
        "total_students": total_students,
    }
