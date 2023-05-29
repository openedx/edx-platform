import os
import tarfile
import tempfile
from unittest.mock import patch

from django.urls import reverse
from path import Path as path
from rest_framework import status
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import SampleCourseFactory

from common.djangoapps.student.tests.factories import StaffFactory
from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.contentstore.rest_api.v1.views.xblock import toggles, handle_xblock


class XblockViewTest(SharedModuleStoreTestCase, APITestCase):
    """
    Test CRUD operations on xblocks
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.course = SampleCourseFactory.create(display_name='test course', run="Testing_course")
        cls.course_key = cls.course.id

        cls.restricted_course = SampleCourseFactory.create(display_name='restricted test course', run="Restricted_course")
        cls.restricted_course_key = cls.restricted_course.id

        cls.password = 'test'
        cls.student = UserFactory(username='dummy', password=cls.password)
        cls.staff = StaffFactory(course_key=cls.course.id, password=cls.password)
        cls.restricted_staff = StaffFactory(course_key=cls.restricted_course.id, password=cls.password)

    # tests that the api is behind a feature flag
    def test_api_behind_feature_flag(self):
        # should return 404 if the feature flag is not enabled
        url = reverse('cms.djangoapps.contentstore:v1:studio_content', args=[self.course_key])

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # a test case for the create operation
    @patch('cms.djangoapps.contentstore.rest_api.v1.views.xblock.handle_xblock', return_value='test')
    @patch('cms.djangoapps.contentstore.rest_api.v1.views.xblock.toggles', use_studio_content_api=True)
    def test_create_an_xblock(self, mock_use_studio_content_api, mock_handle_xblock):
        # create an xblock
        url = reverse('cms.djangoapps.contentstore:v1:studio_content', args=[self.course_key])

        # send a post request that creates an xblock using this json payload:
        # {
        # "parent_locator": self.course_key,
        # "category": "html",
        # "courseKey": self.course_key,
        # }
        response = self.client.post(url, data={
            "parent_locator": self.course_key,
            "category": "html",
            "courseKey": self.course_key,
        }, format='json')
