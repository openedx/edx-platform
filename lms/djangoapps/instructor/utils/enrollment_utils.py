"""
Utility functions for student enrollment operations.

This module contains reusable functions for processing student enrollments
that can be used in both synchronous and asynchronous contexts.
"""

import logging

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

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


def process_single_student_enrollment(
    course_key,
    action,
    identifier,
    auto_enroll=False,
    email_students=False,
    reason=None,
    email_params=None,
    language=None,
):
    """
    Process enrollment/unenrollment for a single student.

    Args:
        course_key: CourseKey object for the course
        action: 'enroll' or 'unenroll'
        identifier: Student identifier (email or username)
        auto_enroll: Whether to auto-enroll in verified track if applicable
        email_students: Whether to send enrollment emails
        reason: Optional reason for enrollment change
        email_params: Pre-computed email parameters (optional)
        language: User's preferred language (optional)

    Returns:
        dict: Result of the enrollment operation with keys:
            - identifier: The student identifier
            - success: Boolean indicating if operation was successful
            - before: State before operation (if successful)
            - after: State after operation (if successful)
            - error_type: Type of error ('invalid_identifier', 'validation_error', 'general_error')
            - error_message: Error message (if failed)
    """
    identified_user = None
    email = None
    enrollment_obj = None
    state_transition = DEFAULT_TRANSITION_STATE

    try:
        # Try to get user by identifier
        try:
            identified_user = get_student_from_identifier(identifier)
            email = identified_user.email
            if not language:
                language = get_user_email_language(identified_user)
        except User.DoesNotExist:
            email = identifier

        # Validate email
        validate_email(email)

        # Use provided email_params or get them if email_students is enabled
        if email_students and email_params is None:
            course = get_course_by_id(course_key)
            email_params = get_email_params(course, auto_enroll, secure=True)
        elif email_params is None:
            email_params = {}

        # Process enrollment/unenrollment
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
            identified_user, email, state_transition, reason, enrollment_obj
        )

        return {
            "identifier": identifier,
            "success": True,
            "before": before.to_dict(),
            "after": after.to_dict(),
            "state_transition": state_transition,
        }

    except ValidationError:
        return {
            "identifier": identifier,
            "success": False,
            "error_type": "invalid_identifier",
            "invalidIdentifier": True,
        }
    except Exception as exc:  # pylint: disable=broad-exception-caught
        log.exception(f"Error processing {action} for {identifier}: {exc}")
        return {
            "identifier": identifier,
            "success": False,
            "error_type": "general_error",
            "error": True,
            "error_message": str(exc),
        }


def get_enrollment_email_params(course_key, auto_enroll, secure=True):
    """
    Get email parameters for enrollment operations.

    Args:
        course_key: CourseKey object for the course
        auto_enroll: Whether auto-enrollment is enabled
        secure: Whether the request is secure (HTTPS)

    Returns:
        dict: Email parameters for enrollment operations
    """
    course = get_course_by_id(course_key)
    return get_email_params(course, auto_enroll, secure=secure)


def process_student_enrollment_batch(
    course_key,
    action,
    identifiers,
    auto_enroll=False,
    email_students=False,
    reason=None,
    secure=True,
    progress_callback=None,
):
    """
    Process a batch of student enrollment/unenrollment operations.

    Args:
        course_key: CourseKey object for the course
        action: 'enroll' or 'unenroll'
        identifiers: List of student identifiers (emails or usernames)
        auto_enroll: Whether to auto-enroll in verified track if applicable
        email_students: Whether to send enrollment emails
        reason: Optional reason for enrollment change
        secure: Whether the request is secure (HTTPS)
        progress_callback: Optional callback function to report progress
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
    # Get email parameters once if email_students is enabled
    email_params = {}
    if email_students:
        email_params = get_enrollment_email_params(course_key, auto_enroll, secure)

    results = []
    successful_operations = 0
    failed_operations = 0
    total_students = len(identifiers)

    for i, identifier in enumerate(identifiers):
        # Process single student
        result = process_single_student_enrollment(
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

        # Call progress callback if provided
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
