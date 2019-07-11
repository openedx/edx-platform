
import pytest

from django.test import TestCase

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator

from openedx.core.djangoapps.appsembler.api.helpers import as_course_key

from openedx.core.djangoapps.appsembler.api.tests.factories import COURSE_ID_STR_TEMPLATE


class CourseKeyHelperTest(TestCase):

    def setUp(self):
        self.course_key_string = COURSE_ID_STR_TEMPLATE.format(1)
        self.course_key = CourseKey.from_string(self.course_key_string)

    def test_from_valid_string(self):
        course_key = as_course_key(self.course_key_string)
        assert isinstance(course_key, CourseKey)
        assert course_key == self.course_key
        assert course_key is not self.course_key

    def test_from_invalid_string(self):
        with pytest.raises(InvalidKeyError):
            as_course_key('some invalid string')

    def test_from_course_key(self):
        course_key = as_course_key(self.course_key)
        assert isinstance(course_key, CourseKey)
        assert course_key == self.course_key
        assert course_key is self.course_key

    def test_from_course_locator(self):
        course_locator = CourseLocator.from_string(
            self.course_key_string)
        course_key = as_course_key(course_locator)
        assert isinstance(course_key, CourseKey)
        assert course_key == self.course_key
        assert course_key is course_locator

    def test_from_invalid_type(self):
        with pytest.raises(TypeError):
            as_course_key(dict(foo='bar'))
