"""
Tests for util.course_key_utils
"""
import ddt
import unittest
from util.course_key_utils import course_key_from_string_or_404
from opaque_keys.edx.keys import CourseKey
from django.http import Http404


@ddt.ddt
class TestFromStringOr404(unittest.TestCase):
    """
    Base Test class for course_key_from_string_or_404 utility tests
    """
    @ddt.data(
        "course-v1:TTT+CS01+2015_T0",  # split style course keys
        "TTT/CS01/2015_T0"  # mongo style course keys
    )
    def test_from_string_or_404_for_valid_course_key(self, valid_course_key):
        """
        Tests course_key_from_string_or_404 for valid split style course keys and mongo style course keys.
        """
        self.assertEquals(
            CourseKey.from_string(valid_course_key),
            course_key_from_string_or_404(valid_course_key)
        )

    @ddt.data(
        "/some.invalid.key/course-v1:TTT+CS01+2015_T0",  # split style course keys
        "/some.invalid.key/TTT/CS01/2015_T0"  # mongo style course keys
    )
    def test_from_string_or_404_for_invalid_course_key(self, invalid_course_key):
        """
        Tests course_key_from_string_or_404 for valid split style course keys and mongo style course keys.
        """
        self.assertRaises(
            Http404,
            course_key_from_string_or_404,
            invalid_course_key,
        )

    @ddt.data(
        "/some.invalid.key/course-v1:TTT+CS01+2015_T0",  # split style invalid course key
        "/some.invalid.key/TTT/CS01/2015_T0"  # mongo style invalid course key
    )
    def test_from_string_or_404_with_message(self, course_string):
        """
        Tests course_key_from_string_or_404 with exception message for split style and monog style invalid course keys.
        :return:
        """
        with self.assertRaises(Http404) as context:
            course_key_from_string_or_404(course_string, message="Invalid Keys")
        self.assertEquals(str(context.exception), "Invalid Keys")
