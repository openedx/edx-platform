"""
Tests for course_info
"""
import json

from mock import patch
from django.conf import settings
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase

from courseware.tests.factories import UserFactory
from xmodule.html_module import CourseInfoModule
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.xml_importer import import_from_xml


class TestCourseInfo(APITestCase):
    """
    Tests for /api/mobile/v0.5/course_info/...
    """
    def setUp(self):
        super(TestCourseInfo, self).setUp()
        self.user = UserFactory.create()
        self.course = CourseFactory.create(mobile_available=True)
        self.client.login(username=self.user.username, password='test')

    def get_response(self, reverse_name, course_id, expected_response_code):
        url = reverse(reverse_name, kwargs={'course_id': unicode(course_id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, expected_response_code)
        return response


class TestAbout(TestCourseInfo):
    """
    Tests for /api/mobile/v0.5/course_info/{course_id}/about
    """
    def get_about_response(self, expected_response_code=200):
        return self.get_response('course-about-detail', self.course.id, expected_response_code)

    def test_about(self):
        response = self.get_about_response()
        self.assertTrue('overview' in response.data)  # pylint: disable=maybe-no-member

    def test_about_static_rewrite(self):
        about_usage_key = self.course.id.make_usage_key('about', 'overview')
        about_module = modulestore().get_item(about_usage_key)
        underlying_about_html = about_module.data

        # check that we start with relative static assets
        self.assertIn('\"/static/', underlying_about_html)

        response = self.get_about_response()
        json_data = json.loads(response.content)
        about_html = json_data['overview']

        # but shouldn't finish with any
        self.assertNotIn('\"/static/', about_html)


class TestUpdates(TestCourseInfo):
    """
    Tests for /api/mobile/v0.5/course_info/{course_id}/updates
    """
    def get_updates_response(self, expected_response_code=200):
        return self.get_response('course-updates-list', self.course.id, expected_response_code)

    def test_updates(self):
        response = self.get_updates_response()
        self.assertEqual(response.data, [])  # pylint: disable=maybe-no-member

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_updates_unreleased_course(self):
        self.get_updates_response(404)

    def test_updates_static_rewrite(self):
        updates_usage_key = self.course.id.make_usage_key('course_info', 'updates')
        course_updates = modulestore().create_item(
            self.user.id,
            updates_usage_key.course_key,
            updates_usage_key.block_type,
            block_id=updates_usage_key.block_id
        )
        course_update_data = {
            "id": 1,
            "date": "Some date",
            "content": "<a href=\"/static/\">foo</a>",
            "status": CourseInfoModule.STATUS_VISIBLE
        }

        course_updates.items = [course_update_data]
        modulestore().update_item(course_updates, self.user.id)

        response = self.get_updates_response()
        content = response.data[0]["content"]  # pylint: disable=maybe-no-member
        self.assertNotIn("\"/static/", content)

        underlying_updates_module = modulestore().get_item(updates_usage_key)
        self.assertIn("\"/static/", underlying_updates_module.items[0]['content'])


class TestHandouts(TestCourseInfo, ModuleStoreTestCase, APITestCase):
    """
    Tests for /api/mobile/v0.5/course_info/{course_id}/handouts
    """
    def setUp(self):
        super(TestHandoutInfo, self).setUp()
        course_items = import_from_xml(self.store, self.user.id, settings.COMMON_TEST_DATA_ROOT, ['toy'])
        self.course = course_items[0]

    def get_handouts_response(self, course_id, expected_response_code=200):
        return self.get_response('course-handouts-list', course_id, expected_response_code)

    def test_no_handouts(self):
        empty_course = CourseFactory.create(mobile_available=True)
        self.get_handouts_response(empty_course.id, 404)

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_handouts_unreleased_course(self):
        self.get_handouts_response(self.course.id, 404)

    def test_handouts_exists(self):
        self.get_handouts_response(self.course.id)

    def test_handouts_static_rewrites(self):
        # check that we start with relative static assets
        handouts_usage_key = self.course.id.make_usage_key('course_info', 'handouts')
        underlying_handouts = self.store.get_item(handouts_usage_key)
        self.assertIn('\'/static/', underlying_handouts.data)

        response = self.get_handouts_response(self.course.id)

        json_data = json.loads(response.content)
        handouts_html = json_data['handouts_html']

        # but shouldn't finish with any
        self.assertNotIn('\'/static/', handouts_html)
