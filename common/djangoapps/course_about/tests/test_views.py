"""
Tests for user enrollment.
"""
import ddt
import json
import unittest

from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.conf import settings
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)
from xmodule.modulestore.tests.factories import CourseFactory, CourseAboutFactory
from student.tests.factories import UserFactory
from util.parsing_utils import course_image_url
from course_about import api
from course_about.errors import CourseNotFoundError, CourseAboutError
from mock import patch
from xmodule.modulestore.django import modulestore
from datetime import datetime

# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.

MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@ddt.ddt
@override_settings(MODULESTORE=MODULESTORE_CONFIG)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CourseInfoTest(ModuleStoreTestCase, APITestCase):
    """
    Test course information.
    """
    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"

    def setUp(self):
        """ Create a course"""
        super(CourseInfoTest, self).setUp()

        self.course = CourseFactory.create()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def test_user_not_authenticated(self):
        # Log out, so we're no longer authenticated
        self.client.logout()

        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        resp_data = json.loads(resp.content)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(resp_data)

    def test_with_valid_course_id(self):
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_with_invalid_course_id(self):
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": 'not/a/validkey'})
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_course_details_all_attributes(self):
        kwargs = dict()
        kwargs["course_id"] = self.course.id
        kwargs["course_runtime"] = self.course.runtime
        CourseAboutFactory.create(**kwargs)
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        resp_data = json.loads(resp.content)
        all_attributes = ['display_name', 'start', 'end', 'announcement', 'advertised_start', 'is_new', 'course_number',
                          'course_id',
                          'effort', 'media', 'course_image']
        for attr in all_attributes:
            self.assertIn(attr, str(resp_data))

    def test_get_course_about_valid_date(self):
        module_store = modulestore()
        self.course.start = datetime.now()
        self.course.end = datetime.now()
        self.course.announcement = datetime.now()
        module_store.update_item(self.course, self.user.id)
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        course_info = json.loads(resp.content)
        self.assertIsNotNone(course_info["start"])
        self.assertIsNotNone(course_info["end"])
        self.assertIsNotNone(course_info["announcement"])

    def test_get_course_about_none_date(self):
        module_store = modulestore()
        self.course.start = None
        self.course.end = None
        self.course.announcement = None
        module_store.update_item(self.course, self.user.id)
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        course_info = json.loads(resp.content)
        self.assertIsNone(course_info["start"])
        self.assertIsNone(course_info["end"])
        self.assertIsNone(course_info["announcement"])

    def test_get_course_details(self):
        kwargs = dict()
        kwargs["course_id"] = self.course.id
        kwargs["course_runtime"] = self.course.runtime
        kwargs["user_id"] = self.user.id
        CourseAboutFactory.create(**kwargs)
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_data = json.loads(resp.content)

        self.assertEqual(unicode(self.course.id), resp_data['course_id'])
        self.assertIn('Run', resp_data['display_name'])

        url = course_image_url(self.course)
        self.assertEquals(url, resp_data['media']['course_image'])

    @patch.object(api, "get_course_about_details")
    def test_get_enrollment_course_not_found_error(self, mock_get_course_about_details):
        mock_get_course_about_details.side_effect = CourseNotFoundError("Something bad happened.")
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @patch.object(api, "get_course_about_details")
    def test_get_enrollment_invalid_key_error(self, mock_get_course_about_details):
        mock_get_course_about_details.side_effect = CourseNotFoundError('a/a/a', "Something bad happened.")
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @patch.object(api, "get_course_about_details")
    def test_get_enrollment_internal_error(self, mock_get_course_about_details):
        mock_get_course_about_details.side_effect = CourseAboutError('error')
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @override_settings(COURSE_ABOUT_DATA_API='foo')
    def test_data_api_config_error(self):
        # Enroll in the course and verify the URL we get sent to
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
