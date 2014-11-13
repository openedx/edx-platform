"""
Unit tests for video-related REST APIs.
"""
# pylint: disable=attribute-defined-outside-init
import json
import datetime
import dateutil.parser
from pytz import UTC

from mock import patch
from unittest import skip
from django.test.utils import override_settings

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url
from contentstore.views.videos import UploadStatus


@patch.dict("django.conf.settings.FEATURES", {'ENABLE_VIDEO_UPLOAD_PIPELINE': True})
class VideoUploadTestCase(CourseTestCase):
    """
    Test cases for the video upload page
    """
    def setUp(self):
        super(VideoUploadTestCase, self).setUp()
        self.url = reverse_course_url('videos_handler', self.course.id)

    def test_video_pipeline_not_configured_error(self):
        response = self.client.ajax_post(
            self.url
        )
        self.assertEqual(response.status_code, 400)

    def test_non_staff_user(self):
        client, __ = self.create_non_staff_authed_user_client()
        response = client.ajax_post(
            self.url
        )
        self.assertEqual(response.status_code, 403)

    @patch('boto.s3.connection.S3Connection')
    @patch('boto.s3.key.Key')
    def setup_and_post_video_uploads(self, s3_key=None, s3_connection=None):  # pylint: disable=unused-argument
        """
        Sets up the course to enable video uploads, posts video files, and returns the response.
        """
        self.institute_name = 'TestUniversity'
        self.files = [
            {'file_name': 'file1'},
            {'file_name': 'file2'},
        ]
        self.course.video_upload_pipeline = {
            'institute_name': self.institute_name,
            'access_token': 'xxx',
        }
        self.store.update_item(self.course, self.user.id)
        response = self.client.ajax_post(
            self.url,
            data={'files': self.files}
        )
        self.assertEqual(response.status_code, 200)
        return response

    def find_in_list(self, value, list_of_dicts, key='file_name'):
        """
        Finds the element in a list of dictionary items whose value of the given key corresponds to the given value.
        """
        return next(el for el in list_of_dicts if el[key] == value)

    def test_success_mock_storage_service(self):
        response = self.setup_and_post_video_uploads()
        for expected_file in self.files:
            self.assertIn(expected_file['file_name'], response.content)

    @skip("disable testing with live servers, but can enable locally with real values")
    @override_settings(AWS_ACCESS_KEY_ID="PUT_IN_TEST_ACCESS_KEY_ID_HERE")
    @override_settings(AWS_SECRET_ACCESS_KEY="PUT_IN_TEST_SECRET_ACCESS_KEY_HERE")
    @override_settings(VIDEO_UPLOAD_PIPELINE={'BUCKET': 'edx-sandbox-test', 'ROOT_PATH': ''})
    @patch('contentstore.views.videos.KEY_EXPIRATION_IN_SECONDS', 60)
    def test_success_test_storage_service(self):
        response = self.setup_and_post_video_uploads()
        returned_files = json.loads(response.content)['files']
        for expected_file in self.files:
            file_name = expected_file['file_name']
            returned_file = self.find_in_list(file_name, returned_files)
            self.assertRegexpMatches(
                returned_file['upload-url'],
                'https://edx-sandbox-test.s3.amazonaws.com/{}/.*{}.*'.format(self.institute_name, file_name),
            )

    def test_video_index(self):
        self.setup_and_post_video_uploads()
        response = self.client.get_json(self.url)
        videos = json.loads(response.content)['videos']
        for expected_file in self.files:
            file_name = expected_file['file_name']
            video = self.find_in_list(file_name, videos)

            # status
            self.assertEquals(video['status'], UploadStatus.uploading)

            # upload date
            upload_date = dateutil.parser.parse(video['date_uploaded'])
            self.assertEquals(upload_date.date(), datetime.datetime.now(UTC).date())
