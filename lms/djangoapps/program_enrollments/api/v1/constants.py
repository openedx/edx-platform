"""
  Constants and strings for the course-enrollment app
"""

# Captures strings composed of alphanumeric characters, dashes, and underscores.
PROGRAM_UUID_PATTERN = r'(?P<program_uuid>[A-Za-z0-9-]+)'


class CourseEnrollmentResponseStatuses(object):
    """
    Class to group response statuses returned by the course enrollment endpoint
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    DUPLICATED = "duplicated"
    INVALID_STATUS = "invalid-status"
    CONFLICT = "conflict"
    ILLEGAL_OPERATION = "illegal-operation"
    NOT_IN_PROGRAM = "not-in-program"
    INTERNAL_ERROR = "internal-error"

    ERROR_STATUSES = (
        DUPLICATED,
        INVALID_STATUS,
        CONFLICT,
        ILLEGAL_OPERATION,
        NOT_IN_PROGRAM,
        INTERNAL_ERROR,
    )
