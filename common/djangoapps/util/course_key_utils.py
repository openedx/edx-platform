"""
Convenience methods for working with course objects
"""
from django.http import Http404
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey


def from_string_or_404(course_key_string):
    """
    Gets CourseKey from the string passed as parameter.

    Parses course key from string(containing course key) or raises 404 if the string's format is invalid.

    Arguments:
        course_key_string(str): It is string containing the course key

    Returns:
        CourseKey: A key that uniquely identifies a course

    Raises:
        HTTP404: A 404 not found exception will be thrown if course_key_string's format is invalid

    """
    try:
        course_key = CourseKey.from_string(course_key_string)
    except InvalidKeyError:
        raise Http404

    return course_key
