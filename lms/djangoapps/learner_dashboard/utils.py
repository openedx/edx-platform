"""
The utility methods and functions to help the djangoapp logic
"""


import six
from opaque_keys.edx.keys import CourseKey

FAKE_COURSE_KEY = CourseKey.from_string('course-v1:fake+course+run')


def strip_course_id(path):
    """
    The utility function to help remove the fake
    course ID from the url path
    """
    course_id = six.text_type(FAKE_COURSE_KEY)
    return path.split(course_id)[0]
