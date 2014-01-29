"""
Test the about xblock
"""
import mock
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from .helpers import LoginEnrollmentTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AboutTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    def setUp(self):
        self.course = CourseFactory.create()
        self.about = ItemFactory.create(
            category="about", parent_location=self.course.location,
            data="OOGIE BLOOGIE", display_name="overview"
        )
        # The following XML course is closed; we're testing that
        # an about page still appears when the course is already closed
        self.xml_course_id = 'edX/detached_pages/2014'
        self.xml_data = "about page 463139"

    def test_logged_in(self):
        self.setup_user()
        url = reverse('about_course', args=[self.course.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)

    def test_anonymous_user(self):
        url = reverse('about_course', args=[self.course.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)

    @mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_logged_in_xml(self):
        self.setup_user()
        url = reverse('about_course', args=[self.xml_course_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.xml_data, resp.content)

    @mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_anonymous_user_xml(self):
        url = reverse('about_course', args=[self.xml_course_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.xml_data, resp.content)
