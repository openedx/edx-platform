"""
Tests for util.course_key_utils
"""
from nose.tools import assert_equals, assert_raises  # pylint: disable=no-name-in-module
from util.course_key_utils import from_string_or_404
from opaque_keys.edx.keys import CourseKey
from django.http import Http404


def test_from_string_or_404():

    #testing with split style course keys
    assert_raises(
        Http404,
        from_string_or_404,
        "/some.invalid.key/course-v1:TTT+CS01+2015_T0"
    )
    assert_equals(
        CourseKey.from_string("course-v1:TTT+CS01+2015_T0"),
        from_string_or_404("course-v1:TTT+CS01+2015_T0")
    )

    #testing with mongo style course keys
    assert_raises(
        Http404,
        from_string_or_404,
        "/some.invalid.key/TTT/CS01/2015_T0"
    )
    assert_equals(
        CourseKey.from_string("TTT/CS01/2015_T0"),
        from_string_or_404("TTT/CS01/2015_T0")
    )
