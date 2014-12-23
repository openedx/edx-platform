from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys import InvalidKeyError
from course_about.serializers import _serialize_content
from course_about.errors import CourseNotFoundError
from lms.djangoapps.courseware import courses
import logging
from opaque_keys.edx.keys import CourseKey

log = logging.getLogger(__name__)

"""
Data Aggregation Layer for the Course About API. All knowledge of edx-platform specific data structures should
be hidden behind this layer.  The Python API (api.py) will access all data directly through this module.

This is responsible for combining data from the following resources:
* CourseDescriptor
* CourseAboutDescriptor

Eventually, additional Marketing metadata will also be accessed through this layer.
"""


def get_course_about_details(request, course_id):  # pylint: disable=unused-argument
    """
    Return course information
    """
    try:
        course_descriptor, course_key = get_course(course_id)  # pylint: disable=W0612
        return _serialize_content(course_descriptor=course_descriptor)
    except:
        msg = u"Some error occurred."
        log.warn(msg)
        raise CourseNotFoundError(msg)


def get_course(course_id, depth=0):
    """
    Utility method to obtain course descriptor object.
    """
    course_descriptor = None
    course_key = get_course_key(course_id)
    if course_key:
        course_descriptor = get_course_descriptor(course_key, depth)

    return course_descriptor, course_key


def get_course_key(course_id, slashseparated=False):
    """
    Utility method to obtain course_key from course_id
    """

    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        try:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        except InvalidKeyError:
            course_key = None
    if slashseparated:
        try:
            course_key = course_key.to_deprecated_string()
        except InvalidKeyError:
            course_key = course_id
    return course_key


def get_course_descriptor(course_key, depth):
    """Returns all course course information for the given course.

    Based on the course course_key, return course info

    Args:
        course_key (CourseLocator) : The course to retrieve course information for.

    Returns:
        Course descriptor object.

    Raises:
        CourseNotFoundError
    """

    try:
        course_descriptor = courses.get_course(course_key, depth)
    except ValueError:
        msg = u"course not found course {course}".format(course=course_key)
        log.warning(msg)
        raise CourseNotFoundError(msg)
    return course_descriptor