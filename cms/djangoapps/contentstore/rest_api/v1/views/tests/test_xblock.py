from unittest.mock import patch
from django.http import JsonResponse

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from cms.djangoapps.contentstore.tests.test_utils import AuthorizeStaffTestCase


class XblockViewPostTest(AuthorizeStaffTestCase, ModuleStoreTestCase, APITestCase):
    """
    Test CRUD operations on xblocks
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def get_url(self, course_key):
        return reverse('cms.djangoapps.contentstore:v1:studio_content', kwargs={'course_id': course_key})

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
    def make_request(
        self,
        mock_use_studio_content_api,
        mock_handle_xblock,
        course_id=None,
        data=None,
        assert_xblock_handler_call=False
    ):
        course_id = course_id if course_id else self.course.id
        course_id_string = course_id.html_id()
        url = self.get_url(course_id_string)
        data = self.get_test_data(course_id_string)

        response = self.client.post(url, data=data)

        # test that xblock_handler has been called with the correct request, url, and data
        if (assert_xblock_handler_call):
            passed_args = mock_handle_xblock.call_args[0][0]

            assert (mock_handle_xblock.call_count == 1)
            assert (passed_args.data.get('courseKey') == course_id_string)
            assert (passed_args.method == 'POST')
            assert (passed_args.path == url)

        return response

    # tests that the api is behind a feature flag
    def test_api_behind_feature_flag(self):
        # should return 404 if the feature flag is not enabled
        url = reverse('cms.djangoapps.contentstore:v1:studio_content', args=[self.course_key])

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_xblock_handler_called_with_correct_arguments(self):
        self.client.login(username=self.course_instructor.username, password=self.password)
        response = self.make_request(assert_xblock_handler_call=True)
        assert response.status_code == status.HTTP_200_OK
