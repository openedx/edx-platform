"""
Constants used throughout the program_enrollments app and exposed to other
in-process apps through api.py.
"""
from __future__ import absolute_import, unicode_literals


class ProgramEnrollmentStatuses(object):
    """
    Status that a user may have enrolled in a program.

    TODO: Define the semantics of each of these (EDUCATOR-4958)
    """
    ENROLLED = 'enrolled'
    PENDING = 'pending'
    SUSPENDED = 'suspended'
    CANCELED = 'canceled'
    __ACTIVE__ = (ENROLLED, PENDING)
    __ALL__ = (ENROLLED, PENDING, SUSPENDED, CANCELED)

    # Note: Any changes to this value will trigger a migration on
    # ProgramEnrollment!
    __MODEL_CHOICES__ = (
        (status, status) for status in __ALL__
    )


class ProgramCourseEnrollmentStatuses(object):
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
