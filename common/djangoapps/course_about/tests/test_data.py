"""
Tests specific to the Data Aggregation Layer of the Course About API.

"""
import ddt
from mock import patch
from nose.tools import raises
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
import unittest

from django.test.utils import override_settings
from django.conf import settings
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.factories import CourseFactory, CourseAboutFactory
from student.tests.factories import UserFactory
from course_about import data
from course_about.errors import CourseNotFoundError

# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.
MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@ddt.ddt
@override_settings(MODULESTORE=MODULESTORE_CONFIG)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CourseAboutDataTest(ModuleStoreTestCase):
    """
    Test course enrollment data aggregation.

    """
    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"

    def setUp(self):
        """Create a course and user, then log in. """
        super(CourseAboutDataTest, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def test_get_course_about_details(self):
        course_info = data.get_course_about_details(unicode(self.course.id))
        self.assertIsNotNone(course_info)

    def test_non_existent_course(self):
        try:
            data.get_course_about_details("this/is/bananas")
        except Exception as e:
            self.assertIsInstance(e, CourseNotFoundError)

    def test_invalid_course_key(self):
        try:
            data._get_course_key("invalidKey")
        except Exception as e:
            self.assertIsInstance(e, InvalidKeyError)

    def test_get_valid_course_key(self):
        d = data._get_course_key("edX/DemoX/Demo_Course")
        self.assertIsInstance(d, CourseKey)

    def test_get_course_descriptor_with_valid_key(self):
        d = data._get_course_descriptor(self.course.id, 0)
        self.assertIsNotNone(d)

    def test_get_course_descriptor_with_invalid_key(self):
        try:
            descriptor = data._get_course_descriptor("this/is/bananas", 0)
        except Exception as e:
            descriptor = None
            self.assertIsInstance(e, ValueError)
        self.assertIsNone(descriptor)