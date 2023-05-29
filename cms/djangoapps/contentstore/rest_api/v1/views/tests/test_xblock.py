import os
import tarfile
import tempfile
from unittest.mock import patch
from django.http import JsonResponse

from django.urls import reverse
from path import Path as path
from rest_framework import status
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import SampleCourseFactory, CourseFactory
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.tests.factories import UserFactory, GlobalStaffFactory, InstructorFactory
from cms.djangoapps.contentstore.rest_api.v1.views.xblock import toggles, handle_xblock


class CourseAPITestMixin():
    """ setup for proctored exam settings tests """

    def setUp(self):
        super().setUp()
        self.course_key = CourseKey.from_string('course-v1:edX+ToyX+Toy_Course')
        self.other_course_key = CourseKey.from_string('course-v1:edX+ToyX_Other_Course+Toy_Course')
        self.course = self.create_course_from_course_key(self.course_key)
        self.other_course = self.create_course_from_course_key(self.other_course_key)
        self.password = 'password'
        self.student = UserFactory.create(username='student', password=self.password)
        self.global_staff = GlobalStaffFactory(username='global-staff', password=self.password)
        self.course_instructor = InstructorFactory(
            username='instructor',
            password=self.password,
            course_key=self.course.id,
        )
        self.other_course_instructor = InstructorFactory(
            username='other-course-instructor',
            password=self.password,
            course_key=self.other_course.id,
        )

    def tearDown(self):
        super().tearDown()
        self.client.logout()

    @classmethod
    def create_course_from_course_key(cls, course_key):
        return CourseFactory.create(
            org=course_key.org,
            course=course_key.course,
            run=course_key.run
        )

    def make_request(self, course_id=None, data=None):
        raise NotImplementedError

    def get_url(self, course_key):
        return reverse('cms.djangoapps.contentstore:v1:studio_content', kwargs={'course_id': course_key})

    def test_403_if_student(self):
        self.client.login(username=self.student.username, password=self.password)
        response = self.make_request()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_403_if_instructor_in_another_course(self):
        self.client.login(
            username=self.other_course_instructor.username,
            password=self.password
        )
        response = self.make_request()
        assert response.status_code == status.HTTP_403_FORBIDDEN


class XblockViewPostTest(CourseAPITestMixin, ModuleStoreTestCase, APITestCase):
    """
    Test CRUD operations on xblocks
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def get_test_data(self, course_id):
        return {
            "parent_locator": course_id,
            "category": "html",
            "courseKey": course_id,
        }

    @patch('cms.djangoapps.contentstore.rest_api.v1.views.xblock.handle_xblock', return_value=JsonResponse({
        'locator': 'test-locator',
        'courseKey': 'test-course-key',
    }))
    @patch('cms.djangoapps.contentstore.rest_api.v1.views.xblock.toggles.use_studio_content_api', return_value=True)
    def make_request(self, mock_use_studio_content_api, mock_handle_xblock, course_id=None, data=None):
        course_id = course_id if course_id else self.course.id
        url = self.get_url(course_id)
        data = self.get_test_data(course_id)

        return self.client.post(url, data=data)

    # tests that the api is behind a feature flag
    def test_api_behind_feature_flag(self):
        # should return 404 if the feature flag is not enabled
        url = reverse('cms.djangoapps.contentstore:v1:studio_content', args=[self.course_key])

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_200_global_staff(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        response = self.make_request()
        assert response.status_code == status.HTTP_200_OK

    def test_200_course_instructor(self):
        self.client.login(username=self.course_instructor.username, password=self.password)
        response = self.make_request()
        assert response.status_code == status.HTTP_200_OK

    # a test case for the create operation
    # def test_create_an_xblock(self, mock_use_studio_content_api, mock_handle_xblock):
    #     key = self.course_key.html_id()
    #     # create an xblock
    #     url = reverse('cms.djangoapps.contentstore:v1:studio_content', args=[key])

    #     # send a post request
    #     response = self.client.post(url, data={
    #         "parent_locator": key,
    #         "category": "html",
    #         "courseKey": key,
    #     }, format='json')

    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
