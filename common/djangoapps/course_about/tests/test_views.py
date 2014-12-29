"""
Tests for user enrollment.
"""
from datetime import datetime, timedelta
import ddt
from ddt import unpack, data
import json
import unittest

from mock import patch
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.conf import settings
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)
from xmodule.modulestore.tests.factories import CourseFactory, CourseAboutFactory
from course_about import api
from course_about.errors import CourseNotFoundError
from student.tests.factories import UserFactory, CourseModeFactory
from django.contrib.auth.models import User
from cms.djangoapps.contentstore.utils import course_image_url


# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.

MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@ddt.ddt
@override_settings(MODULESTORE=MODULESTORE_CONFIG)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CourseInfoTest(ModuleStoreTestCase, APITestCase):
    """
    Test user enrollment, especially with different course modes.
    """

    def setUp(self):
        """ Create a course"""
        super(CourseInfoTest, self).setUp()

    @unpack
    @data({"org": "test", "course": "course1", "display_name": "testing display name", "start": datetime.now(),
           "end": datetime.now() + timedelta(days=2),
           "video": "testing-video-link", 'effort': 'Testing effort', 'is_new': True,
           'course_image': 'http://image-course/'})
    def test_get_course_details(self, **kwargs):
        self.course = CourseFactory.create(**kwargs)
        kwargs["course_id"] = self.course.id
        kwargs["course_runtime"] = self.course.runtime
        CourseAboutFactory.create(**kwargs)
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.content)

        self.assertEqual(unicode(self.course.id), data['course_id'])
        self.assertEqual('testing display name', data['display_name'])

        url = course_image_url(self.course)
        self.assertEquals(url, data['media']['course_image'])
        self.assertEqual('testing-video-link', data['media']['video'])


    def test_invalid_get_course_details(self, **kwargs):
        self.course = CourseFactory.create(**kwargs)
        kwargs["course_id"] = self.course.id
        kwargs["course_runtime"] = self.course.runtime
        CourseAboutFactory.create(**kwargs)
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_id'])
        self.assertNotEqual('testing display name', data['display_name'])
