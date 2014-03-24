"""
Test the course_info xblock
"""
import mock
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from .helpers import LoginEnrollmentTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class CourseInfoTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    def setUp(self):
        self.course = CourseFactory.create()
        self.page = ItemFactory.create(
            category="course_info", parent_location=self.course.location,
            data="OOGIE BLOOGIE", display_name="updates"
        )
        # The following XML course is closed; we're testing that
        # a course info page still appears when the course is already closed
        self.xml_data = "course info 463139"
        self.xml_course_id = "edX/detached_pages/2014"

    def test_logged_in(self):
        self.setup_user()
        url = reverse('info', args=[self.course.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)

    def test_anonymous_user(self):
        url = reverse('info', args=[self.course.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("OOGIE BLOOGIE", resp.content)

    @mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_logged_in_xml(self):
        self.setup_user()
        url = reverse('info', args=[self.xml_course_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.xml_data, resp.content)

    @mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_anonymous_user_xml(self):
        url = reverse('info', args=[self.xml_course_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(self.xml_data, resp.content)
