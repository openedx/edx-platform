"""
Constants used throughout the program_enrollments app and exposed to other
in-process apps through api.py.
"""


class ProgramEnrollmentStatuses(object):
    """
    Status that a user may have enrolled in a program.

    Note: Changing the value of __ALL__ will trigger a migration.

    TODO: Define the semantics of each of these (EDUCATOR-4958)
    """
    ENROLLED = 'enrolled'
    PENDING = 'pending'
    SUSPENDED = 'suspended'
    CANCELED = 'canceled'
    __ACTIVE__ = (ENROLLED, PENDING)
    __ALL__ = (ENROLLED, PENDING, SUSPENDED, CANCELED)


class ProgramCourseEnrollmentStatuses(object):
    """
    Status that a user may have enrolled in a course.

    Note: Changing the value of __ALL__ will trigger a migration.

    TODO: Consider whether we need these (EDUCATOR-4958)
    """
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    __ALL__ = (ACTIVE, INACTIVE)
