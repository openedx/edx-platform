#-*- coding: utf-8 -*-
"""
Unit tests for video-related REST APIs.
"""
import csv
import ddt
import json
import dateutil.parser
import re
from StringIO import StringIO

from django.conf import settings
from django.test.utils import override_settings
from mock import Mock, patch

from edxval.api import create_profile, create_video, get_video_info

from contentstore.models import VideoUploadConfig
from contentstore.views.videos import KEY_EXPIRATION_IN_SECONDS, StatusDisplayStrings
from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url
from xmodule.modulestore.tests.factories import CourseFactory


class VideoUploadTestMixin(object):
    """
    Test cases for the video upload feature
    """
    def get_url_for_course_key(self, course_key, kwargs=None):
        """Return video handler URL for the given course"""
        return reverse_course_url(self.VIEW_NAME, course_key, kwargs)

    def setUp(self):
        super(VideoUploadTestMixin, self).setUp()
        self.url = self.get_url_for_course_key(self.course.id)
        self.test_token = "test_token"
        self.course.video_upload_pipeline = {
            "course_video_upload_token": self.test_token,
        }
        self.save_course()

        # create another course for videos belonging to multiple courses
        self.course2 = CourseFactory.create()
        self.course2.video_upload_pipeline = {
            "course_video_upload_token": self.test_token,
        }
        self.course2.save()
        self.store.update_item(self.course2, self.user.id)

        # course ids for videos
        course_ids = [unicode(self.course.id), unicode(self.course2.id)]

        self.profiles = ["profile1", "profile2"]
        self.previous_uploads = [
            {
                "edx_video_id": "test1",
                "client_video_id": "test1.mp4",
                "duration": 42.0,
                "status": "upload",
                "courses": course_ids,
                "encoded_videos": [],
            },
            {
                "edx_video_id": "test2",
                "client_video_id": "test2.mp4",
                "duration": 128.0,
                "status": "file_complete",
                "courses": course_ids,
                "encoded_videos": [
                    {
                        "profile": "profile1",
                        "url": "http://example.com/profile1/test2.mp4",
                        "file_size": 1600,
                        "bitrate": 100,
                    },
                    {
                        "profile": "profile2",
                        "url": "http://example.com/profile2/test2.mov",
                        "file_size": 16000,
                        "bitrate": 1000,
                    },
                ],
            },
            {
                "edx_video_id": "non-ascii",
                "client_video_id": u"nón-ascii-näme.mp4",
                "duration": 256.0,
                "status": "transcode_active",
                "courses": course_ids,
                "encoded_videos": [
                    {
                        "profile": "profile1",
                        "url": u"http://example.com/profile1/nón-ascii-näme.mp4",
                        "file_size": 3200,
                        "bitrate": 100,
                    },
                ]
            },
        ]
        # Ensure every status string is tested
        self.previous_uploads += [
            {
                "edx_video_id": "status_test_{}".format(status),
                "client_video_id": "status_test.mp4",
                "duration": 3.14,
                "status": status,
                "courses": course_ids,
                "encoded_videos": [],
            }
            for status in (
                StatusDisplayStrings._STATUS_MAP.keys() +  # pylint:disable=protected-access
                ["non_existent_status"]
            )
        ]
        for profile in self.profiles:
            create_profile(profile)
        for video in self.previous_uploads:
            create_video(video)

    def _get_previous_upload(self, edx_video_id):
        """Returns the previous upload with the given video id."""
        return next(
            video
            for video in self.previous_uploads
            if video["edx_video_id"] == edx_video_id
        )

    def test_anon_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_put(self):
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, 405)

    def test_invalid_course_key(self):
        response = self.client.get(
            self.get_url_for_course_key("Non/Existent/Course")
        )
        self.assertEqual(response.status_code, 404)

    def test_non_staff_user(self):
        client, __ = self.create_non_staff_authed_user_client()
        response = client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_video_pipeline_not_enabled(self):
        settings.FEATURES["ENABLE_VIDEO_UPLOAD_PIPELINE"] = False
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_video_pipeline_not_configured(self):
        settings.VIDEO_UPLOAD_PIPELINE = None
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_course_not_configured(self):
        self.course.video_upload_pipeline = {}
        self.save_course()
        self.assertEqual(self.client.get(self.url).status_code, 404)


@ddt.ddt
@patch.dict("django.conf.settings.FEATURES", {"ENABLE_VIDEO_UPLOAD_PIPELINE": True})
@override_settings(VIDEO_UPLOAD_PIPELINE={"BUCKET": "test_bucket", "ROOT_PATH": "test_root"})
class VideosHandlerTestCase(VideoUploadTestMixin, CourseTestCase):
    """Test cases for the main video upload endpoint"""

    VIEW_NAME = "videos_handler"

    def test_get_json(self):
        response = self.client.get_json(self.url)
        self.assertEqual(response.status_code, 200)
        response_videos = json.loads(response.content)["videos"]
        self.assertEqual(len(response_videos), len(self.previous_uploads))
        for i, response_video in enumerate(response_videos):
            # Videos should be returned by creation date descending
            original_video = self.previous_uploads[-(i + 1)]
            self.assertEqual(
                set(response_video.keys()),
                set(["edx_video_id", "client_video_id", "created", "duration", "status"])
            )
            dateutil.parser.parse(response_video["created"])
            for field in ["edx_video_id", "client_video_id", "duration"]:
                self.assertEqual(response_video[field], original_video[field])
            self.assertEqual(
                response_video["status"],
                StatusDisplayStrings.get(original_video["status"])
            )

    def test_get_html(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertRegexpMatches(response["Content-Type"], "^text/html(;.*)?$")
        # Crude check for presence of data in returned HTML
        for video in self.previous_uploads:
            self.assertIn(video["edx_video_id"], response.content)

    def test_post_non_json(self):
        response = self.client.post(self.url, {"files": []})
        self.assertEqual(response.status_code, 400)

    def test_post_malformed_json(self):
        response = self.client.post(self.url, "{", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_post_invalid_json(self):
        def assert_bad(content):
            """Make request with content and assert that response is 400"""
            response = self.client.post(
                self.url,
                json.dumps(content),
                content_type="application/json"
            )
            self.assertEqual(response.status_code, 400)

        # Top level missing files key
        assert_bad({})

        # Entry missing file_name
        assert_bad({"files": [{"content_type": "video/mp4"}]})

        # Entry missing content_type
        assert_bad({"files": [{"file_name": "test.mp4"}]})

    @override_settings(AWS_ACCESS_KEY_ID="test_key_id", AWS_SECRET_ACCESS_KEY="test_secret")
    @patch("boto.s3.key.Key")
    @patch("boto.s3.connection.S3Connection")
    @ddt.data(
        (
            [
                {
                    "file_name": "supported-1.mp4",
                    "content_type": "video/mp4",
                },
                {
                    "file_name": "supported-2.mov",
                    "content_type": "video/quicktime",
                },
            ],
            200
        ),
        (
            [
                {
                    "file_name": "unsupported-1.txt",
                    "content_type": "text/plain",
                },
                {
                    "file_name": "unsupported-2.png",
                    "content_type": "image/png",
                },
            ],
            400
        )
    )
    @ddt.unpack
    def test_video_supported_file_formats(self, files, expected_status, mock_conn, mock_key):
        """
        Test that video upload works correctly against supported and unsupported file formats.
        """
        bucket = Mock()
        mock_conn.return_value = Mock(get_bucket=Mock(return_value=bucket))
        mock_key_instances = [
            Mock(
                generate_url=Mock(
                    return_value="http://example.com/url_{}".format(file_info["file_name"])
                )
            )
            for file_info in files
        ]
        # If extra calls are made, return a dummy
        mock_key.side_effect = mock_key_instances + [Mock()]

        # Check supported formats
        response = self.client.post(
            self.url,
            json.dumps({"files": files}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, expected_status)
        response = json.loads(response.content)

        if expected_status == 200:
            self.assertNotIn('error', response)
        else:
            self.assertIn('error', response)
            self.assertEqual(response['error'], "Request 'files' entry contain unsupported content_type")

    @override_settings(AWS_ACCESS_KEY_ID='test_key_id', AWS_SECRET_ACCESS_KEY='test_secret')
    @patch('boto.s3.connection.S3Connection')
    def test_upload_with_non_ascii_charaters(self, mock_conn):
        """
        Test that video uploads throws error message when file name contains special characters.
        """
        file_name = u'test\u2019_file.mp4'
        files = [{'file_name': file_name, 'content_type': 'video/mp4'}]

        bucket = Mock()
        mock_conn.return_value = Mock(get_bucket=Mock(return_value=bucket))

        response = self.client.post(
            self.url,
            json.dumps({'files': files}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response = json.loads(response.content)
        self.assertEqual(response['error'], 'The file name for %s must contain only ASCII characters.' % file_name)

    @override_settings(AWS_ACCESS_KEY_ID="test_key_id", AWS_SECRET_ACCESS_KEY="test_secret")
    @patch("boto.s3.key.Key")
    @patch("boto.s3.connection.S3Connection")
    def test_post_success(self, mock_conn, mock_key):
        files = [
            {
                "file_name": "first.mp4",
                "content_type": "video/mp4",
            },
            {
                "file_name": "second.mp4",
                "content_type": "video/mp4",
            },
            {
                "file_name": "third.mov",
                "content_type": "video/quicktime",
            },
            {
                "file_name": "fourth.mp4",
                "content_type": "video/mp4",
            },
        ]

        bucket = Mock()
        mock_conn.return_value = Mock(get_bucket=Mock(return_value=bucket))
        mock_key_instances = [
            Mock(
                generate_url=Mock(
                    return_value="http://example.com/url_{}".format(file_info["file_name"])
                )
            )
            for file_info in files
        ]
        # If extra calls are made, return a dummy
        mock_key.side_effect = mock_key_instances + [Mock()]

        response = self.client.post(
            self.url,
            json.dumps({"files": files}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        response_obj = json.loads(response.content)

        mock_conn.assert_called_once_with(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        self.assertEqual(len(response_obj["files"]), len(files))
        self.assertEqual(mock_key.call_count, len(files))
        for i, file_info in enumerate(files):
            # Ensure Key was set up correctly and extract id
            key_call_args, __ = mock_key.call_args_list[i]
            self.assertEqual(key_call_args[0], bucket)
            path_match = re.match(
                (
                    settings.VIDEO_UPLOAD_PIPELINE["ROOT_PATH"] +
                    "/([a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12})$"
                ),
                key_call_args[1]
            )
            self.assertIsNotNone(path_match)
            video_id = path_match.group(1)
            mock_key_instance = mock_key_instances[i]
            mock_key_instance.set_metadata.assert_any_call(
                "course_video_upload_token",
                self.test_token
            )
            mock_key_instance.set_metadata.assert_any_call(
                "client_video_id",
                file_info["file_name"]
            )
            mock_key_instance.set_metadata.assert_any_call("course_key", unicode(self.course.id))
            mock_key_instance.generate_url.assert_called_once_with(
                KEY_EXPIRATION_IN_SECONDS,
                "PUT",
                headers={"Content-Type": file_info["content_type"]}
            )

            # Ensure VAL was updated
            val_info = get_video_info(video_id)
            self.assertEqual(val_info["status"], "upload")
            self.assertEqual(val_info["client_video_id"], file_info["file_name"])
            self.assertEqual(val_info["status"], "upload")
            self.assertEqual(val_info["duration"], 0)
            self.assertEqual(val_info["courses"], [unicode(self.course.id)])

            # Ensure response is correct
            response_file = response_obj["files"][i]
            self.assertEqual(response_file["file_name"], file_info["file_name"])
            self.assertEqual(response_file["upload_url"], mock_key_instance.generate_url())

    def _assert_video_removal(self, url, edx_video_id, deleted_videos):
        """
        Verify that if correct video is removed from a particular course.

        Arguments:
            url (str): URL to get uploaded videos
            edx_video_id (str): video id
            deleted_videos (int): how many videos are deleted
        """
        response = self.client.get_json(url)
        self.assertEqual(response.status_code, 200)
        response_videos = json.loads(response.content)["videos"]
        self.assertEqual(len(response_videos), len(self.previous_uploads) - deleted_videos)

        if deleted_videos:
            self.assertNotIn(edx_video_id, [video.get('edx_video_id') for video in response_videos])
        else:
            self.assertIn(edx_video_id, [video.get('edx_video_id') for video in response_videos])

    def test_video_removal(self):
        """
        Verifies that video removal is working as expected.
        """
        edx_video_id = 'test1'
        remove_url = self.get_url_for_course_key(self.course.id, {'edx_video_id': edx_video_id})
        response = self.client.delete(remove_url, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 204)

        self._assert_video_removal(self.url, edx_video_id, 1)

    def test_video_removal_multiple_courses(self):
        """
        Verifies that video removal is working as expected for multiple courses.

        If a video is used by multiple courses then removal from one course shouldn't effect the other course.
        """
        # remove video from course1
        edx_video_id = 'test1'
        remove_url = self.get_url_for_course_key(self.course.id, {'edx_video_id': edx_video_id})
        response = self.client.delete(remove_url, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 204)

        # verify that video is only deleted from course1 only
        self._assert_video_removal(self.url, edx_video_id, 1)
        self._assert_video_removal(self.get_url_for_course_key(self.course2.id), edx_video_id, 0)


@patch.dict("django.conf.settings.FEATURES", {"ENABLE_VIDEO_UPLOAD_PIPELINE": True})
@override_settings(VIDEO_UPLOAD_PIPELINE={"BUCKET": "test_bucket", "ROOT_PATH": "test_root"})
class VideoUrlsCsvTestCase(VideoUploadTestMixin, CourseTestCase):
    """Test cases for the CSV download endpoint for video uploads"""

    VIEW_NAME = "video_encodings_download"

    def setUp(self):
        super(VideoUrlsCsvTestCase, self).setUp()
        VideoUploadConfig(profile_whitelist="profile1").save()

    def _check_csv_response(self, expected_profiles):
        """
        Check that the response is a valid CSV response containing rows
        corresponding to previous_uploads and including the expected profiles.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            "attachment; filename={course}_video_urls.csv".format(course=self.course.id.course)
        )
        response_reader = StringIO(response.content)
        reader = csv.DictReader(response_reader, dialect=csv.excel)
        self.assertEqual(
            reader.fieldnames,
            (
                ["Name", "Duration", "Date Added", "Video ID", "Status"] +
                ["{} URL".format(profile) for profile in expected_profiles]
            )
        )
        rows = list(reader)
        self.assertEqual(len(rows), len(self.previous_uploads))
        for i, row in enumerate(rows):
            response_video = {
                key.decode("utf-8"): value.decode("utf-8") for key, value in row.items()
            }
            # Videos should be returned by creation date descending
            original_video = self.previous_uploads[-(i + 1)]
            self.assertEqual(response_video["Name"], original_video["client_video_id"])
            self.assertEqual(response_video["Duration"], str(original_video["duration"]))
            dateutil.parser.parse(response_video["Date Added"])
            self.assertEqual(response_video["Video ID"], original_video["edx_video_id"])
            self.assertEqual(response_video["Status"], StatusDisplayStrings.get(original_video["status"]))
            for profile in expected_profiles:
                response_profile_url = response_video["{} URL".format(profile)]
                original_encoded_for_profile = next(
                    (
                        original_encoded
                        for original_encoded in original_video["encoded_videos"]
                        if original_encoded["profile"] == profile
                    ),
                    None
                )
                if original_encoded_for_profile:
                    self.assertEqual(response_profile_url, original_encoded_for_profile["url"])
                else:
                    self.assertEqual(response_profile_url, "")

    def test_basic(self):
        self._check_csv_response(["profile1"])

    def test_profile_whitelist(self):
        VideoUploadConfig(profile_whitelist="profile1,profile2").save()
        self._check_csv_response(["profile1", "profile2"])

    def test_non_ascii_course(self):
        course = CourseFactory.create(
            number=u"nón-äscii",
            video_upload_pipeline={
                "course_video_upload_token": self.test_token,
            }
        )
        response = self.client.get(self.get_url_for_course_key(course.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            "attachment; filename=video_urls.csv; filename*=utf-8''n%C3%B3n-%C3%A4scii_video_urls.csv"
        )
