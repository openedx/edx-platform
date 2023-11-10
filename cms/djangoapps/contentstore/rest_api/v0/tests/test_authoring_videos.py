"""
Tests for the videos views of the Authoring API. This tests only the view itself,
not the underlying Xblock service.
"""
from unittest.mock import patch
from django.http import JsonResponse

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from cms.djangoapps.contentstore.tests.test_utils import AuthorizeStaffTestCase


TEST_RESPONSE_DATA = "test-response-data"
VERSION = "v0"
EDX_VIDEO_ID = "0000-2322-2323-2323"
EXAMPLE_VIDEO_DATA = {
    "files": [{"file_name": "video.mp4", "content_type": "video/mp4"}]
}


class MockCourseKey():
    """
    Mock CourseKey class
    """

    def __init__(self, course_id):
        self.course_id = course_id

    def html_id(self):
        return self.course_id


################ Videos Uploads Tests ################


class VideosUploadsViewTestCase(AuthorizeStaffTestCase):
    """
    This base class supports tests with the various HTTP methods (GET, POST, PUT, PATCH, and DELETE).
    Tests for each such message are organized by classes that derive from this one (e.g., XBlockViewGetTest).
    Each derived class supplies get_test_data() to govern what goes into the body of the HTTP request.
    Each derived class optionally overrides get_url_params() to govern request parameter values.
    Additionally, each derived class supplies send_request() to bring it all together when making a request.
    """

    def get_test_data(self):
        raise NotImplementedError("get_test_data must be implemented by subclasses")

    def get_url_params(self):
        """
        Returns a dictionary of parameters to be used in the url that includes course_id and usage_key_string.
        Override this method if you don't want to use the default values.
        """
        raise NotImplementedError("get_url_params must be implemented by subclasses")

    def get_url(self, _course_id=None):
        return reverse(
            f"cms.djangoapps.contentstore:{VERSION}:cms_api_videos_uploads",
            kwargs=self.get_url_params(),
        )

    def send_request(self, _url, _data):
        raise NotImplementedError("send_request must be implemented by subclasses")

    @patch(
        f"cms.djangoapps.contentstore.rest_api.{VERSION}.views.authoring_videos.handle_videos",
        return_value=JsonResponse(
            {
                "test_response_data": TEST_RESPONSE_DATA,
                "course_key": AuthorizeStaffTestCase.get_course_key_string(),
            }
        ),
    )
    @patch(
        f"cms.djangoapps.contentstore.rest_api.{VERSION}.views.authoring_videos.toggles.use_studio_content_api",
        return_value=True,
    )
    def make_request(
        self,
        mock_use_studio_content_api,
        mock_handle_videos,
        run_assertions=None,
        course_id=None,
        data=None,
    ):
        """
        Note that the actual videos handler is mocked out and not used here. Patches used with this method serve to
        test that routing of HTTP requests to the videos handler is correct, that the intended HTTP method has been
        used, that data fed into the handler is as expected, and that data returned by the handler is as expected.
        Inputs and outputs are handled through send_request() polymorphism, to cover all the HTTP methods in a
        common fashion here.
        Validations are through injection of run_assertions().
        """
        url = self.get_url()
        data = self.get_test_data()

        response = self.send_request(url, data)

        # run optional callback method with additional assertions
        if run_assertions:
            run_assertions(response=response, mock_handle_videos=mock_handle_videos)

        return response


class VideosUploadsViewGetTest(
    VideosUploadsViewTestCase, ModuleStoreTestCase, APITestCase
):
    """
    Test GET operation on videos
    """

    def get_test_data(self):
        return None

    def get_url_params(self):
        """
        Returns a dictionary of parameters to be used in the url that includes course_id and usage_key_string.
        Override this method if you don't want to use the default values.
        """
        return {"course_id": self.get_course_key_string(), "edx_video_id": None}

    def assert_videos_handler_called(self, *, mock_handle_videos, response):
        """
        This defines a callback method that is called after the request is made
        and runs additional assertions on the response and mock_handle_videos.
        """
        mock_handle_videos.assert_called_once()
        passed_args = mock_handle_videos.call_args[0][0]

        assert passed_args.method == "GET"
        assert passed_args.path == self.get_url()

    def send_request(self, url, data):
        return self.client.get(url)

    def test_api_behind_feature_flag(self):
        # should return 404 if the feature flag is not enabled
        url = self.get_url()

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_videos_handler_called_with_correct_arguments(self):
        self.client.login(
            username=self.course_instructor.username, password=self.password
        )
        response = self.make_request(  # pylint: disable=no-value-for-parameter
            run_assertions=self.assert_videos_handler_called,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["test_response_data"] == TEST_RESPONSE_DATA


class VideosUploadsViewDeleteTest(
    VideosUploadsViewTestCase, ModuleStoreTestCase, APITestCase
):
    """
    Test POST operation on videos
    """

    def get_test_data(self):
        return {None}

    def get_url_params(self):
        """
        Returns a dictionary of parameters to be used in the url that includes course_id and usage_key_string.
        Override this method if you don't want to use the default values.
        """
        return {"course_id": self.get_course_key_string(), "edx_video_id": EDX_VIDEO_ID}

    def assert_videos_handler_called(self, *, mock_handle_videos, response):
        """
        This defines a callback method that is called after the request is made
        and runs additional assertions on the response and mock_handle_videos.
        """
        mock_handle_videos.assert_called_once()
        passed_args = mock_handle_videos.call_args[0][0]

        assert passed_args.method == "DELETE"
        assert passed_args.path == self.get_url()

    def send_request(self, url, data):
        return self.client.delete(url)

    def test_api_behind_feature_flag(self):
        # should return 404 if the feature flag is not enabled
        url = self.get_url()

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_videos_handler_called_with_correct_arguments(self):
        self.client.login(
            username=self.course_instructor.username, password=self.password
        )
        response = self.make_request(  # pylint: disable=no-value-for-parameter
            run_assertions=self.assert_videos_handler_called,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["test_response_data"] == TEST_RESPONSE_DATA


class VideosUploadsViewPostTest(
    VideosUploadsViewTestCase, ModuleStoreTestCase, APITestCase
):
    """
    Test POST operation on videos
    """

    def get_test_data(self):
        return EXAMPLE_VIDEO_DATA

    def get_url(self, _course_id=None):
        return reverse(
            f"cms.djangoapps.contentstore:{VERSION}:cms_api_create_videos_upload",
            kwargs=self.get_url_params(),
        )

    def get_url_params(self):
        """
        Returns a dictionary of parameters to be used in the url that includes course_id and usage_key_string.
        Override this method if you don't want to use the default values.
        """
        return {"course_id": self.get_course_key_string()}

    def assert_videos_handler_called(self, *, mock_handle_videos, response):
        """
        This defines a callback method that is called after the request is made
        and runs additional assertions on the response and mock_handle_videos.
        """
        mock_handle_videos.assert_called_once()
        passed_args = mock_handle_videos.call_args[0][0]

        assert passed_args.method == "POST"
        assert passed_args.path == self.get_url()

    def send_request(self, url, data):
        return self.client.post(url, data=data)

    def test_api_behind_feature_flag(self):
        # should return 404 if the feature flag is not enabled
        url = self.get_url()

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_videos_handler_called_with_correct_arguments(self):
        self.client.login(
            username=self.course_instructor.username, password=self.password
        )
        response = self.make_request(  # pylint: disable=no-value-for-parameter
            run_assertions=self.assert_videos_handler_called,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["test_response_data"] == TEST_RESPONSE_DATA
