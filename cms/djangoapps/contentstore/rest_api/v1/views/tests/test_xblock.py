from unittest.mock import patch
from django.http import JsonResponse

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from cms.djangoapps.contentstore.tests.test_utils import AuthorizeStaffTestCase


TEST_LOCATOR = "block-v1:dede+aba+weagi+type@problem+block@ba6327f840da49289fb27a9243913478"


class XblockViewTestCase(AuthorizeStaffTestCase):
    # assumes that you want to pass a block id to the url

    def get_test_data():
        raise NotImplementedError("get_test_data must be implemented by subclasses")

    def get_url_params(self):
        return {"course_id": AuthorizeStaffTestCase.get_course_key_string(), "usage_key_string": TEST_LOCATOR}

    def get_url(self, course_key):
        return reverse(
            "cms.djangoapps.contentstore:v1:studio_content",
            kwargs=self.get_url_params(course_key),
        )

    def send_request():
        raise NotImplementedError("send_request must be implemented by subclasses")

    @patch(
        "cms.djangoapps.contentstore.rest_api.v1.views.xblock.handle_xblock",
        return_value=JsonResponse(
            {
                "locator": TEST_LOCATOR,
                "courseKey": AuthorizeStaffTestCase.get_course_key_string(),
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
        course_id = self.get_course_key_string()
        url = self.get_url(course_id)
        data = self.get_test_data(id)

        response = self.send_request(url, data)

        # run optional callback method with additional assertions
        if run_assertions:
            run_assertions(
                response=response, mock_handle_xblock=mock_handle_xblock
            )

        return response


class XblockViewGetTest(XblockViewTestCase, ModuleStoreTestCase, APITestCase):
    """
    Test GET operation on xblocks
    """

    def get_test_data(self, course_id):
        return None

    def assert_xblock_handler_called(self, *, mock_handle_xblock, course_id, response):
        mock_handle_xblock.assert_called_once()
        passed_args = mock_handle_xblock.call_args[0][0]

        assert passed_args.method == "GET"
        assert passed_args.path == self.get_url(course_id)

    def send_request(self, url, data):
        return self.client.get(url)

    def test_api_behind_feature_flag(self):
        # should return 404 if the feature flag is not enabled
        url = self.get_url(self.course_key)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_xblock_handler_called_with_correct_arguments(self):
        self.client.login(
            username=self.course_instructor.username, password=self.password
        )
        response = self.make_request(
            run_assertions=self.assert_xblock_handler_called,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["locator"] == TEST_LOCATOR
        assert data["courseKey"] == 'abc'


class XblockViewPostTest(XblockViewTestCase, ModuleStoreTestCase, APITestCase):
    """
    Test POST operation on xblocks
    """

    def get_url_params(self, course_key):
        return {"course_id": course_key}

    def get_url(self, course_key):
        return reverse(
            "cms.djangoapps.contentstore:v1:studio_content",
            kwargs=self.get_url_params(course_key),
        )

    def get_test_data(self, course_id):
        return {
            "parent_locator": course_id,
            "category": "html",
            "courseKey": course_id,
        }

    def assert_xblock_handler_called(self, *, mock_handle_xblock, response):
        mock_handle_xblock.assert_called_once()
        passed_args = mock_handle_xblock.call_args[0][0]

        import pdb
        pdb.set_trace()
        course_id = self.get_course_key_string()

        assert passed_args.data.get("courseKey") == course_id
        assert passed_args.method == "POST"
        assert passed_args.path == self.get_url(course_id)

    def send_request(self, url, data):
        import pdb
        pdb.set_trace()
        return self.client.post(url, data=data)

    def test_api_behind_feature_flag(self):
        # should return 404 if the feature flag is not enabled
        url = self.get_url(self.course_key)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_xblock_handler_called_with_correct_arguments(self):
        self.client.login(
            username=self.course_instructor.username, password=self.password
        )
        response = self.make_request(
            run_assertions=self.assert_xblock_handler_called,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        import pdb
        pdb.set_trace()
        assert data["locator"] == TEST_LOCATOR
        assert data["courseKey"] == self.get_course_key_string()
