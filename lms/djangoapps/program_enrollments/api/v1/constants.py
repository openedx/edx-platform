"""
  Constants and strings for the course-enrollment app
"""

# Captures strings composed of alphanumeric characters a-f and dashes.
PROGRAM_UUID_PATTERN = r'(?P<program_uuid>[A-Fa-f0-9-]+)'
MAX_ENROLLMENT_RECORDS = 25

# The name of the key that identifies students for POST/PATCH requests
REQUEST_STUDENT_KEY = 'student_key'

ENABLE_ENROLLMENT_RESET_FLAG = 'ENABLE_ENROLLMENT_RESET'


class BaseEnrollmentResponseStatuses(object):
    """
    Class to group common response statuses
    """
    DUPLICATED = 'duplicated'
    INVALID_STATUS = "invalid-status"
    CONFLICT = "conflict"
    ILLEGAL_OPERATION = "illegal-operation"
    NOT_IN_PROGRAM = "not-in-program"
    INTERNAL_ERROR = "internal-error"

    ERROR_STATUSES = {
        DUPLICATED,
        INVALID_STATUS,
        CONFLICT,
        ILLEGAL_OPERATION,
        NOT_IN_PROGRAM,
        INTERNAL_ERROR,
    }


class CourseEnrollmentResponseStatuses(BaseEnrollmentResponseStatuses):
    """
    Class to group response statuses returned by the course enrollment endpoint
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    NOT_FOUND = "not-found"

    ERROR_STATUSES = BaseEnrollmentResponseStatuses.ERROR_STATUSES | {NOT_FOUND}


class ProgramEnrollmentResponseStatuses(BaseEnrollmentResponseStatuses):
    """
    Class to group response statuses returned by the program enrollment endpoint
    """
    ENROLLED = 'enrolled'
    PENDING = 'pending'
    SUSPENDED = 'suspended'
    CANCELED = 'canceled'

    VALID_STATUSES = [ENROLLED, PENDING, SUSPENDED, CANCELED]


class CourseRunProgressStatuses(object):
    """
    Class to group statuses that a course run can be in with respect to user progress.
    """
    IN_PROGRESS = 'in_progress'
    UPCOMING = 'upcoming'
    COMPLETED = 'completed'
