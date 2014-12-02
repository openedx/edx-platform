"""
Tests for course_info
"""
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase

from courseware.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.xml_importer import import_from_xml


class TestCourseInfo(ModuleStoreTestCase, APITestCase):
    """
    Tests for /api/mobile/v0.5/course_info/...
    """
    def setUp(self):
        super(TestCourseInfo, self).setUp()
        self.user = UserFactory.create()
        self.course = CourseFactory.create(mobile_available=True)
        self.client.login(username=self.user.username, password='test')

    def test_about(self):
        url = reverse('course-about-detail', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('overview' in response.data)  # pylint: disable=maybe-no-member

    # def test_about_static_rewrites(self):
    #     about_usage_key = self.course.id.make_usage_key('about', 'overview')
    #     about_module = self.store.get_item(about_usage_key)
    #     about_html = about_module.render(STUDENT_VIEW)
    #     print "about is %s" % about_html
    #     self.assertEqual(about_html, False)

    def test_no_handouts(self):
        url = reverse('course-handouts-list', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_handout_exists(self):
        course_items = import_from_xml(self.store, self.user.id, settings.COMMON_TEST_DATA_ROOT, ['toy'])
        course = course_items[0]
        url = reverse('course-handouts-list', kwargs={'course_id': unicode(course.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_handout_static_rewrites(self):
        course_items = import_from_xml(self.store, self.user.id, settings.COMMON_TEST_DATA_ROOT, ['toy'])
        course = course_items[0]

        # check that we start with relative static assets
        handouts_usage_key = course.id.make_usage_key('course_info', 'handouts')
        underlying_handouts = self.store.get_item(handouts_usage_key)
        self.assertIn('\'/static/', underlying_handouts.data)

        url = reverse('course-handouts-list', kwargs={'course_id': unicode(course.id)})
        response = self.client.get(url)

        json_data = json.loads(response.content)
        handouts_html = json_data['handouts_html']

        # but shouldn't finish with any
        self.assertNotIn('\'/static/', handouts_html)

        self.assertEqual(response.status_code, 200)

    def test_updates(self):
        url = reverse('course-updates-list', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])  # pylint: disable=maybe-no-member
        # TODO: add handouts and updates, somehow
