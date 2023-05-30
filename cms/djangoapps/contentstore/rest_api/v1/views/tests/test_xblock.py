from unittest.mock import patch
from django.http import JsonResponse

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from cms.djangoapps.contentstore.tests.test_utils import AuthorizeStaffTestCase


class XblockViewTestCase(AuthorizeStaffTestCase):
    def get_url(self, course_key, block_id=None):
        kwargs = (
            {"course_id": course_key}
            if block_id is None
            else {"course_id": course_key, "usage_key_string": block_id}
        )
        return reverse("cms.djangoapps.contentstore:v1:studio_content", kwargs=kwargs)

    def send_request():
        raise NotImplementedError("send_request must be implemented by subclasses")

    @patch(
        "cms.djangoapps.contentstore.rest_api.v1.views.xblock.handle_xblock",
        return_value=JsonResponse(
            {
                "locator": "test-locator",
                "courseKey": "test-course-key",
            }
        ),
    )
    @patch(
        "cms.djangoapps.contentstore.rest_api.v1.views.xblock.toggles.use_studio_content_api",
        return_value=True,
    )
    def make_request(
        self,
        mock_use_studio_content_api,
        mock_handle_xblock,
        run_assertions=None,
        course_id=None,
        data=None,
    ):
        id = self.get_course_id_string(course_id=course_id)
        url = self.get_url(id)
        data = self.get_test_data(id)

        response = self.send_request(url, data)

        # run optional callback method with additional assertions
        if run_assertions:
            run_assertions(
                response=response, course_id=id, mock_handle_xblock=mock_handle_xblock
            )

        return response

    def get_course_id_string(self, course_id=None):
        course_id = course_id if course_id else self.course.id
        return course_id.html_id()


class XblockViewPostTest(XblockViewTestCase, ModuleStoreTestCase, APITestCase):
    """
    Test CRUD operations on xblocks
    """

    def get_test_data(self, course_id):
        return {
            "parent_locator": course_id,
            "category": "html",
            "courseKey": course_id,
        }

    def assert_xblock_handler_called(self, *, mock_handle_xblock, course_id):
        mock_handle_xblock.assert_called_once()
        passed_args = mock_handle_xblock.call_args[0][0]

        assert passed_args.data.get("courseKey") == course_id
        assert passed_args.method == "POST"
        assert passed_args.path == self.get_url(course_id)

    def send_request(self, url, data):
        return self.client.post(url, data=data)

    def test_api_behind_feature_flag(self):
        # should return 404 if the feature flag is not enabled
        url = reverse(
            "cms.djangoapps.contentstore:v1:studio_content", args=[self.course_key]
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_xblock_handler_called_with_correct_arguments(self):
        self.client.login(
            username=self.course_instructor.username, password=self.password
        )
        response = self.make_request(
            assert_xblock_handler_call=True,
            run_assertions=self.assert_xblock_handler_called,
        )
        assert response.status_code == status.HTTP_200_OK
