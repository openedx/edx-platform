# lint-amnesty, pylint: disable=missing-module-docstring

class CourseIdMissingException(Exception):
    """
    course_id missing
    """


class UserDoesNotExistException(Exception):
    """
    course_id invalid
    """


class EnrollmentModeMismatchError(Exception):
    """
    requester has outdated information about the currently active enrollment
    """


class EnrollmentAttributesMissingError(Exception):
    """
    some enrollment attributes are missing
    """
