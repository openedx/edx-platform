"""
Python API functions related to reading program enrollments.

Outside of this subpackage, import these functions
from `lms.djangoapps.program_enrollments.api`.
"""
from __future__ import absolute_import, unicode_literals

from ..models import ProgramCourseEnrollment, ProgramEnrollment

_STUDENT_ARG_ERROR_MESSAGE = (
    "user and external_user_key are both None; at least one must be provided."
)
_REALIZED_FILTER_ERROR_TEMPLATE = (
    "{} and {} are mutually exclusive; at most one of them may be passed in as True."
)


def get_program_enrollment(
        program_uuid,
        user=None,
        external_user_key=None,
        curriculum_uuid=None,
):
    """
    TODO
    """
    if not (user or external_user_key):
        raise ValueError(_STUDENT_ARG_ERROR_MESSAGE)
    filters = {
        "user": user,
        "external_user_key": external_user_key,
        "curriculum_uuid": curriculum_uuid,
    }
    return ProgramEnrollment.objects.get(
        program_uuid=program_uuid, **_remove_none_values(filters)

    )


def fetch_program_enrollments(
        program_uuid,
        curriculum_uuids=None,
        users=None,
        external_user_keys=None,
        program_enrollment_statuses=None,
        realized_only=False,
        waiting_only=False,
):
    """
    TODO
    """
    if realized_only and waiting_only:
        raise ValueError(
            _REALIZED_FILTER_ERROR_TEMPLATE.format("realized_only", "waiting_only")
        )
    filters = {
        "curriculum_uuid__in": curriculum_uuids,
        "user__in": users,
        "external_user_key__in": external_user_keys,
        "status__in": program_enrollment_statuses,
    }
    if realized_only:
        filters["user__isnull"] = False
    if waiting_only:
        filters["user__isnull"] = True
    return ProgramEnrollment.objects.filter(
        program_uuid=program_uuid, **_remove_none_values(filters)
    )


def fetch_program_enrollments_by_student(
        user=None,
        external_user_key=None,
        program_uuids=None,
        curriculum_uuids=None,
        program_enrollment_statuses=None,
        realized_only=False,
        waiting_only=False,
):
    """
    TODO
    """
    if not (user or external_user_key):
        raise ValueError(_STUDENT_ARG_ERROR_MESSAGE)
    if realized_only and waiting_only:
        raise ValueError(
            _REALIZED_FILTER_ERROR_TEMPLATE.format("realized_only", "waiting_only")
        )
    filters = {
        "user": user,
        "external_user_key": external_user_key,
        "program_uuid__in": program_uuids,
        "curriculum_uuid__in": curriculum_uuids,
        "status__in": program_enrollment_statuses,
    }
    if realized_only:
        filters["user__isnull"] = False
    if waiting_only:
        filters["user__isnull"] = True
    return ProgramEnrollment.objects.filter(**_remove_none_values(filters))


def get_program_course_enrollment(
        program_uuid,
        course_key,
        user=None,
        external_user_key=None,
        curriculum_uuid=None,
        realized_only=False,
        waiting_only=False,
):
    """
    TODO
    """
    if not (user or external_user_key):
        raise ValueError(_STUDENT_ARG_ERROR_MESSAGE)
    if realized_only and waiting_only:
        raise ValueError(
            _REALIZED_FILTER_ERROR_TEMPLATE.format("realized_only", "waiting_only")
        )
    filters = {
        "program_enrollment__user": user,
        "program_enrollment__external_user_key": external_user_key,
        "program_enrollment__curriculum_uuid": curriculum_uuid,
    }
    if realized_only:
        filters["program_enrollment__user__isnull"] = False
    if waiting_only:
        filters["program_enrollment__user__isnull"] = True
    return ProgramCourseEnrollment.objects.get(
        program_enrollment__program_uuid=program_uuid,
        course_key=course_key,
        **_remove_none_values(filters)
    )


def fetch_program_course_enrollments(
        program_uuid,
        course_key,
        curriculum_uuids=None,
        users=None,
        external_user_keys=None,
        program_enrollment_statuses=None,
        active_only=False,
        inactive_only=False,
        realized_only=False,
        waiting_only=False,
):
    """
    TODO
    """
    if active_only and inactive_only:
        raise ValueError(
            _REALIZED_FILTER_ERROR_TEMPLATE.format("active_only", "inactive_only")
        )
    if realized_only and waiting_only:
        raise ValueError(
            _REALIZED_FILTER_ERROR_TEMPLATE.format("realized_only", "waiting_only")
        )
    filters = {
        "program_enrollment__curriculum_uuid__in": curriculum_uuids,
        "program_enrollment__user__in": users,
        "program_enrollment__external_user_key__in": external_user_keys,
        "program_enrollment__status__in": program_enrollment_statuses,
    }
    if active_only:
        filters["status"] = "active"
    if inactive_only:
        filters["status"] = "inactive"
    if realized_only:
        filters["program_enrollment__user__isnull"] = False
    if waiting_only:
        filters["program_enrollment__user__isnull"] = True
    return ProgramCourseEnrollment.objects.filter(
        program_enrollment__program_uuid=program_uuid,
        course_key=course_key,
        **_remove_none_values(filters)
    )


def fetch_program_course_enrollments_by_student(
        user=None,
        external_user_key=None,
        program_uuids=None,
        curriculum_uuids=None,
        course_keys=None,
        program_enrollment_statuses=None,
        active_only=False,
        inactive_only=False,
):
    """
    TODO
    """
    if not (user or external_user_key):
        raise ValueError(_STUDENT_ARG_ERROR_MESSAGE)
    if active_only and inactive_only:
        raise ValueError(
            _REALIZED_FILTER_ERROR_TEMPLATE.format("active_only", "inactive_only")
        )
    filters = {
        "program_enrollment__user": user,
        "program_enrollment__external_user_key": external_user_key,
        "program_enrollment__program_uuid__in": program_uuids,
        "program_enrollment__curriculum_uuid__in": curriculum_uuids,
        "course_key__in": course_keys,
        "program_enrollment__status__in": program_enrollment_statuses,
    }
    if active_only:
        filters["status"] = "active"
    if inactive_only:
        filters["status"] = "inactive"
    return ProgramCourseEnrollment.objects.filter(**_remove_none_values(filters))


def _remove_none_values(dictionary):
    """
    TODO
    """
    return {
        key: value for key, value in dictionary.items() if value is not None
    }
