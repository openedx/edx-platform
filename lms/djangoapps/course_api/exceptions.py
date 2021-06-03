"""
Course API custom exceptions
"""


class OverEnrollmentLimitException(Exception):
    """
    Exception used by `get_course_members` to signal when a
    course has more enrollments than the limit specified on
    `settings.COURSE_MEMBER_API_ENROLLMENT_LIMIT`.
    """
