"""
Tests specific to the Data Aggregation Layer of the Course About API.

"""
import unittest
from datetime import datetime
from django.conf import settings
from nose.tools import raises
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory
from course_about import data
from course_about.errors import CourseNotFoundError
from xmodule.modulestore.django import modulestore


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

    def test_get_course_about_valid_date(self):
        module_store = modulestore()
        self.course.start = datetime.now()
        self.course.end = datetime.now()
        self.course.announcement = datetime.now()
        module_store.update_item(self.course, self.user.id)
        course_info = data.get_course_about_details(unicode(self.course.id))
        self.assertIsNotNone(course_info["start"])
        self.assertIsNotNone(course_info["end"])
        self.assertIsNotNone(course_info["announcement"])

    def test_get_course_about_none_date(self):
        module_store = modulestore()
        self.course.start = None
        self.course.end = None
        self.course.announcement = None
        module_store.update_item(self.course, self.user.id)
        course_info = data.get_course_about_details(unicode(self.course.id))
        self.assertIsNone(course_info["start"])
        self.assertIsNone(course_info["end"])
        self.assertIsNone(course_info["announcement"])

    @raises(CourseNotFoundError)
    def test_non_existent_course(self):
        data.get_course_about_details("this/is/bananas")

    @raises(CourseNotFoundError)
    def test_invalid_key(self):
        data.get_course_about_details("invalid:key:k")
