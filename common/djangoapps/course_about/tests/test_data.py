"""
Tests specific to the Data Aggregation Layer of the Course About API.

"""
import ddt
from nose.tools import raises
from opaque_keys import InvalidKeyError
import unittest
from django.test.utils import override_settings
from django.conf import settings
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)
from xmodule.modulestore.tests.factories import CourseFactory
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
            data.get_course_about_details("this/is/invalid")
        except Exception as ex:
            self.assertEquals(ex.__class__, CourseNotFoundError)

    @raises(InvalidKeyError)
    def test_non_existent_course_key(self):
        try:
            data.get_course_about_details("invalidKey")
        except Exception as ex:
            self.assertEquals(ex.__class__, InvalidKeyError)