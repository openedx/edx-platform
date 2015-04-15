"""Data Aggregation Layer for the Course About API.
This is responsible for combining data from the following resources:
* CourseDescriptor
* CourseAboutDescriptor
"""
import logging
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from course_about.serializers import serialize_content
from course_about.errors import CourseNotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


log = logging.getLogger(__name__)

ABOUT_ATTRIBUTES = [
    'effort',
    'overview',
    'title',
    'university',
    'number',
    'short_description',
    'description',
    'key_dates',
    'video',
    'course_staff_short',
    'course_staff_extended',
    'requirements',
    'syllabus',
    'textbook',
    'faq',
    'more_info',
    'ocw_links',
]


def get_course_about_details(course_id):  # pylint: disable=unused-argument
    """
    Return course information for a given course id.
    Args:
        course_id(str) : The course id to retrieve course information for.

    Returns:
        Serializable dictionary of the Course About Information.

    Raises:
        CourseNotFoundError
    """
    try:
        course_key = CourseKey.from_string(course_id)
        course_descriptor = modulestore().get_course(course_key)
        if course_descriptor is None:
            raise CourseNotFoundError("course not found")
    except InvalidKeyError as err:
        raise CourseNotFoundError(err.message)

    about_descriptor = {
        attribute: _fetch_course_detail(course_key, attribute)
        for attribute in ABOUT_ATTRIBUTES
    }

    course_info = serialize_content(course_descriptor=course_descriptor, about_descriptor=about_descriptor)
    return course_info


def _fetch_course_detail(course_key, attribute):
    """
    Fetch the course about attribute for the given course's attribute from persistence and return its value.
    """
    usage_key = course_key.make_usage_key('about', attribute)
    try:
        value = modulestore().get_item(usage_key).data
    except ItemNotFoundError:
        value = None
    return value
