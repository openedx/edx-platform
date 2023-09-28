"""
Constants used throughout the program_enrollments app and exposed to other
in-process apps through api.py.
"""
from common.djangoapps.student.roles import CourseStaffRole


class ProgramEnrollmentStatuses:
    """
    Status that a user may have enrolled in a program.

    TODO: Define the semantics of each of these (EDUCATOR-4958)
    """
    ENROLLED = 'enrolled'
    PENDING = 'pending'
    SUSPENDED = 'suspended'
    CANCELED = 'canceled'
    ENDED = 'ended'
    __ACTIVE__ = (ENROLLED, PENDING)
    __ALL__ = (ENROLLED, PENDING, SUSPENDED, CANCELED, ENDED)

    # Note: Any changes to this value will trigger a migration on
    # ProgramEnrollment!
    __MODEL_CHOICES__ = (
        (status, status) for status in __ALL__
    )


class ProgramCourseEnrollmentStatuses:
    """
    Status that a user may have enrolled in a course.

    TODO: Consider whether we need these (EDUCATOR-4958)
    """
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    __ALL__ = (ACTIVE, INACTIVE)

    # Note: Any changes to this value will trigger a migration on
    # ProgramCourseEnrollment!
    __MODEL_CHOICES__ = (
        (status, status) for status in __ALL__
    )


class _EnrollmentErrorStatuses:
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


class ProgramOperationStatuses(
        ProgramEnrollmentStatuses,
        _EnrollmentErrorStatuses,
):
    """
    Valid program enrollment operation statuses.

    Combines error statuses and OK statuses.
    """
    __OK__ = ProgramEnrollmentStatuses.__ALL__
    __ERRORS__ = _EnrollmentErrorStatuses.__ALL__
    __ALL__ = __OK__ + __ERRORS__


class ProgramCourseOperationStatuses(
        ProgramCourseEnrollmentStatuses,
        _EnrollmentErrorStatuses,
):
    """
    Valid program-course enrollment operation statuses.

    Combines error statuses and OK statuses.
    """

    # Could not modify program-course enrollment because the user
    # is not enrolled in the course in the first place.
    NOT_FOUND = "not-found"

    __OK__ = ProgramCourseEnrollmentStatuses.__ALL__
    __ERRORS__ = (NOT_FOUND,) + _EnrollmentErrorStatuses.__ALL__
    __ALL__ = __OK__ + __ERRORS__


class ProgramCourseEnrollmentRoles:
    """
    Valid roles that can be assigned as part of a ProgramCourseEnrollment
    """
    COURSE_STAFF = CourseStaffRole.ROLE
    __ALL__ = (COURSE_STAFF,)

    # Note: Any changes to this value will trigger a migration on
    # CourseAccessRoleAssignment!
    __MODEL_CHOICES__ = (
        (role, role) for role in __ALL__
    )
