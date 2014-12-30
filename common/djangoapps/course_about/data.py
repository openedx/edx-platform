"""Data Aggregation Layer for the Course About API.
This is responsible for combining data from the following resources:
* CourseDescriptor
* CourseAboutDescriptor
"""
from opaque_keys import InvalidKeyError
from course_about.serializers import _serialize_content
from course_about.errors import CourseNotFoundError
from lms.djangoapps.courseware import courses
import logging
from opaque_keys.edx.keys import CourseKey

log = logging.getLogger(__name__)


def get_course_about_details(course_id):  # pylint: disable=unused-argument
    """
    Return course information for a given course id.
    Args:
        course_id : The course id to retrieve course information for.
    Returns:
        Course descriptor object.

    Raises:
        InvalidKeyError , ValueError
    """
    try:
        course_descriptor = _get_course(course_id)  # pylint: disable=W0612
        return _serialize_content(course_descriptor=course_descriptor)
    except InvalidKeyError as err:
        raise InvalidKeyError(err.message)
    except ValueError as err:
        raise CourseNotFoundError(err.message)
    except Exception as err:
        raise ValueError(err.message)


def _get_course(course_id, depth=0):
    """
    Utility method to obtain course descriptor object.
    Args:
        course_key (CourseLocator) : The course to retrieve course information for.

    Returns:
        Course descriptor object.

    Raises:
        InvalidKeyError , ValueError
    """
    try:
        course_key = _get_course_key(course_id)
        course_descriptor = get_course_descriptor(course_key, depth)
    except InvalidKeyError as err:
        raise InvalidKeyError(err.message)
    except ValueError as err:
        raise ValueError(err.message)
    return course_descriptor


def _get_course_key(course_id):
    """
    Utility method to obtain course_key from course_id
    Args:
        course_id (Course Id) : The course_id to get course_key for.

    Returns:
        CourseKey object.

    Raises:
        InvalidKeyError
    """
    course_key = CourseKey.from_string(course_id)
    return course_key


def get_course_descriptor(course_key, depth):
    """Returns all course course information for the given course key.

    Based on the course course_key, return course info

    Args:
        course_key : The course to retrieve course information for.
        depth : deep level to childs return

    Returns:
        Course descriptor object.
    """
    return courses.get_course(course_key, depth)