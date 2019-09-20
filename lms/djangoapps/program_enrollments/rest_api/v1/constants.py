"""
Constants used throughout the program_enrollments V1 API.
"""
from __future__ import absolute_import, unicode_literals

from lms.djangoapps.program_enrollments.constants import ProgramCourseEnrollmentStatuses, ProgramEnrollmentStatuses

# Captures strings composed of alphanumeric characters a-f and dashes.
PROGRAM_UUID_PATTERN = r'(?P<program_uuid>[A-Fa-f0-9-]+)'

# Maximum number of students that may be enrolled at once.
MAX_ENROLLMENT_RECORDS = 25

# The name of the key that identifies students for POST/PATCH requests
REQUEST_STUDENT_KEY = 'student_key'

# This flag should only be enabled on sandboxes.
# It enables the endpoint that wipes all program enrollments.
ENABLE_ENROLLMENT_RESET_FLAG = 'ENABLE_ENROLLMENT_RESET'


class _EnrollmentErrorStatuses(object):
    """
    Error statuses common to program and program-course enrollments responses.
    """

    # Same student key supplied more than once.
    DUPLICATED = 'duplicated'

    # Requested target status is invalid
    INVALID_STATUS = "invalid-status"

    # In the case of a POST request, the enrollment already exists.
    CONFLICT = "conflict"

    # Although the request is syntactically valid,
    # the change being made is not supported.
    # For example, it may be illegal to change a user's status back to A
    # after changing it to B, where A and B are two hypothetical enrollment
    # statuses.
    ILLEGAL_OPERATION = "illegal-operation"

    # Could not modify program enrollment or create program-course
    # enrollment because the student is not enrolled in the program in the
    # first place.
    NOT_IN_PROGRAM = "not-in-program"

    # Something unexpected went wrong.
    # If API users are seeing this, we need to investigate.
    INTERNAL_ERROR = "internal-error"

    __ALL__ = (
        DUPLICATED,
        INVALID_STATUS,
        CONFLICT,
        ILLEGAL_OPERATION,
        NOT_IN_PROGRAM,
        INTERNAL_ERROR,
    )


class ProgramResponseStatuses(
        ProgramEnrollmentStatuses,
        _EnrollmentErrorStatuses,
):
    """
    Valid program enrollment response statuses.

    Combines error statuses and OK statuses.
    """
    __OK__ = ProgramEnrollmentStatuses.__ALL__
    __ERRORS__ = _EnrollmentErrorStatuses.__ALL__
    __ALL__ = __OK__ + __ERRORS__


class ProgramCourseResponseStatuses(
        ProgramCourseEnrollmentStatuses,
        _EnrollmentErrorStatuses,
):
    """
    Valid program-course enrollment response statuses.

    Combines error statuses and OK statuses.
    """

    # Could not modify program-course enrollment because the user
    # is not enrolled in the course in the first place.
    NOT_FOUND = "not-found"

    __OK__ = ProgramCourseEnrollmentStatuses.__ALL__
    __ERRORS__ = (NOT_FOUND,) + _EnrollmentErrorStatuses.__ALL__
    __ALL__ = __OK__ + __ERRORS__


class CourseRunProgressStatuses(object):
    """
    Statuses that a course run can be in with respect to user progress.
    """
    IN_PROGRESS = 'in_progress'
    UPCOMING = 'upcoming'
    COMPLETED = 'completed'

    __ALL__ = (
        IN_PROGRESS,
        UPCOMING,
        COMPLETED,
    )
