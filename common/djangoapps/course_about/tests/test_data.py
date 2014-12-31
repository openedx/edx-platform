"""
Tests specific to the Data Aggregation Layer of the Course About API.

"""
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
from util.parsing_utils import parse_video_tag

# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.
MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


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
        self.assertRaises(CourseNotFoundError, data.get_course_about_details, "this/is/bananas")

    def test_parsing_utils_valid_data(self):
        video_html = '<iframe width="560" height="315" src="//www.youtube.com/embed/myvdolink?rel=0" frameborder="0" ' \
                     'allowfullscreen=""></iframe>'
        video_id = parse_video_tag(video_html)
        self.assertIsNotNone(video_id)

    def test_parsing_utils_invalid_data(self):
        video_html = '<iframe width="560" height="315" src="//www.google.com?rel=0" frameborder="0" ' \
                     'allowfullscreen=""></iframe>'
        video_id = parse_video_tag(video_html)
        self.assertIsNone(video_id)

    def test_parsing_utils_no_data(self):
        video_html = None
        video_id = parse_video_tag(video_html)
        self.assertIsNone(video_id)
