"""
Tests for util.course_key_utils
"""
from nose.tools import assert_equals, assert_raises  # pylint: disable=no-name-in-module
from util.course_key_utils import from_string_or_404
from opaque_keys.edx.keys import CourseKey
from django.http import Http404
import ddt
import unittest


@ddt.ddt
class TestFromStringOr404(unittest.TestCase):
    """
    Base Test class for from_string_or_404 utility tests
    """
    @ddt.data(
        ("/some.invalid.key/course-v1:TTT+CS01+2015_T0", "course-v1:TTT+CS01+2015_T0"),  # split style course keys
        ("/some.invalid.key/TTT/CS01/2015_T0", "TTT/CS01/2015_T0"),  # mongo style course keys
    )
    def test_from_string_or_404(self, (invalid_course_key, valid_course_key)):
        """
        Tests from_string_or_404 for valid and invalid split style course keys and mongo style course keys.
        """
        assert_raises(
            Http404,
            from_string_or_404,
            invalid_course_key,
        )
        assert_equals(
            CourseKey.from_string(valid_course_key),
            from_string_or_404(valid_course_key)
        )

    @ddt.data(
        "/some.invalid.key/course-v1:TTT+CS01+2015_T0",  # split style invalid course key
        "/some.invalid.key/TTT/CS01/2015_T0"  # mongo style invalid course key
    )
    def test_from_string_or_404_with_message(self, course_string):
        """
        Tests from_string_or_404 with exception message for split style and monog style invalid course keys.
        :return:
        """
        try:
            from_string_or_404(course_string, message="Invalid Keys")
        except Http404 as exception:
            assert_equals(str(exception), "Invalid Keys")
