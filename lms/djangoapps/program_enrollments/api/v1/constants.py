"""
  Constants and strings for the course-enrollment app
"""

# Captures strings composed of alphanumeric characters a-f and dashes.
PROGRAM_UUID_PATTERN = r'(?P<program_uuid>[A-Fa-f0-9-]+)'
MAX_ENROLLMENT_RECORDS = 25

# The name of the key that identifies students for POST/PATCH requests
REQUEST_STUDENT_KEY = 'student_key'


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
    NOT_FOUND = "not-found"
    INTERNAL_ERROR = "internal-error"

    ERROR_STATUSES = (
        DUPLICATED,
        INVALID_STATUS,
        CONFLICT,
        ILLEGAL_OPERATION,
        NOT_IN_PROGRAM,
        NOT_FOUND,
        INTERNAL_ERROR,
    )


class CourseRunProgressStatuses(object):
    """
    Class to group statuses that a course run can be in with respect to user progress.
    """
    IN_PROGRESS = 'in_progress'
    UPCOMING = 'upcoming'
    COMPLETED = 'completed'
