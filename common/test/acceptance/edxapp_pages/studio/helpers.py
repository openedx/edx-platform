"""
Helper functions for Studio page objects.
"""

class InvalidCourseID(Exception):
    """
    The course ID does not have the correct format.
    """
    pass


def parse_course_id(course_id):
    """
    Parse a `course_id` string of the form "org.number.run"
    and return the components as a tuple.

    Raises an `InvalidCourseID` exception if the course ID is not in the right format.
    """
    if course_id is None:
        raise InvalidCourseID("Invalid course ID: '{0}'".format(course_id))

    elements = course_id.split('.')

    # You need at least 3 parts to a course ID: org, number, and run
    if len(elements) < 3:
        raise InvalidCourseID("Invalid course ID: '{0}'".format(course_id))

    return tuple(elements)
