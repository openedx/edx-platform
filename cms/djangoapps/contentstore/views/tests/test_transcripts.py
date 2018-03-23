"""Tests for items views."""

import copy
from codecs import BOM_UTF8
import ddt
import json
from mock import patch, Mock
import tempfile
import textwrap
from uuid import uuid4

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from edxval.api import create_video
from opaque_keys.edx.keys import UsageKey

from contentstore.tests.utils import CourseTestCase, mock_requests_get
from openedx.core.djangoapps.contentserver.caching import del_cached_content
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.video_module.transcripts_utils import (
    get_video_transcript_content,
    remove_subs_from_store,
    Transcript,
)

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex

SRT_TRANSCRIPT_CONTENT = """
1
00:00:10,500 --> 00:00:13,000
Elephant's Dream

2
00:00:15,000 --> 00:00:18,000
At the left we can see...
"""


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class BaseTranscripts(CourseTestCase):
    """Base test class for transcripts tests."""

    def clear_subs_content(self):
        """Remove, if transcripts content exists."""
        for youtube_id in self.get_youtube_ids().values():
            filename = 'subs_{0}.srt.sjson'.format(youtube_id)
            content_location = StaticContent.compute_location(self.course.id, filename)
            try:
                content = contentstore().find(content_location)
                contentstore().delete(content.get_id())
            except NotFoundError:
                pass

    def save_subs_to_store(self, subs, subs_id):
        """
        Save transcripts into `StaticContent`.
        """
        filedata = json.dumps(subs, indent=2)
        mime_type = 'application/json'
        filename = 'subs_{0}.srt.sjson'.format(subs_id)

        content_location = StaticContent.compute_location(self.course.id, filename)
        content = StaticContent(content_location, filename, mime_type, filedata)
        contentstore().save(content)
        del_cached_content(content_location)
        return content_location

    def setUp(self):
        """Create initial data."""
        super(BaseTranscripts, self).setUp()

        # Add video module
        data = {
            'parent_locator': unicode(self.course.location),
            'category': 'video',
            'type': 'video'
        }
        resp = self.client.ajax_post('/xblock/', data)
        self.assertEqual(resp.status_code, 200)

        self.video_usage_key = self._get_usage_key(resp)
        self.item = modulestore().get_item(self.video_usage_key)
        # hI10vDNYz4M - valid Youtube ID with transcripts.
        # JMD_ifUUfsU, AKqURZnYqpk, DYpADpL7jAY - valid Youtube IDs without transcripts.
        self.item.data = '<video youtube="0.75:JMD_ifUUfsU,1.0:hI10vDNYz4M,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" />'
        modulestore().update_item(self.item, self.user.id)

        self.item = modulestore().get_item(self.video_usage_key)
        # Remove all transcripts for current module.
        self.clear_subs_content()

    def _get_usage_key(self, resp):
        """ Returns the usage key from the response returned by a create operation. """
        usage_key_string = json.loads(resp.content).get('locator')
        return UsageKey.from_string(usage_key_string)

    def get_youtube_ids(self):
        """Return youtube speeds and ids."""
        item = modulestore().get_item(self.video_usage_key)

        return {
            0.75: item.youtube_id_0_75,
            1: item.youtube_id_1_0,
            1.25: item.youtube_id_1_25,
            1.5: item.youtube_id_1_5
        }


@ddt.ddt
class TestUploadTranscripts(BaseTranscripts):
    """
    Tests for '/transcripts/upload' endpoint.
    """
    def setUp(self):
        super(TestUploadTranscripts, self).setUp()
        self.contents = {
            'good': SRT_TRANSCRIPT_CONTENT,
            'bad': 'Some BAD data',
        }
        # Create temporary transcript files
        self.good_srt_file = self.create_transcript_file(content=self.contents['good'], suffix='.srt')
        self.bad_data_srt_file = self.create_transcript_file(content=self.contents['bad'], suffix='.srt')
        self.bad_name_srt_file = self.create_transcript_file(content=self.contents['good'], suffix='.bad')
        self.bom_srt_file = self.create_transcript_file(content=self.contents['good'], suffix='.srt', include_bom=True)

        # Setup a VEDA produced video and persist `edx_video_id` in VAL.
        create_video({
            'edx_video_id': u'123-456-789',
            'status': 'upload',
            'client_video_id': u'Test Video',
            'duration': 0,
            'encoded_videos': [],
            'courses': [unicode(self.course.id)]
        })

        # Add clean up handler
        self.addCleanup(self.clean_temporary_transcripts)

    def create_transcript_file(self, content, suffix, include_bom=False):
        """
        Setup a transcript file with suffix and content.
        """
        transcript_file = tempfile.NamedTemporaryFile(suffix=suffix)
        wrapped_content = textwrap.dedent(content)
        if include_bom:
            wrapped_content = wrapped_content.encode('utf-8-sig')
            # Verify that ufeff(BOM) character is in content.
            self.assertIn(BOM_UTF8, wrapped_content)

        transcript_file.write(wrapped_content)
        transcript_file.seek(0)

        return transcript_file

    def clean_temporary_transcripts(self):
        """
        Close transcript files gracefully.
        """
        self.good_srt_file.close()
        self.bad_data_srt_file.close()
        self.bad_name_srt_file.close()
        self.bom_srt_file.close()

    def upload_transcript(self, locator, transcript_file):
        """
        Uploads a transcript for a video
        """
        payload = {}
        if locator:
            payload.update({'locator': locator})

        if transcript_file:
            payload.update({'transcript-file': transcript_file})

        upload_url = reverse('upload_transcripts')
        response = self.client.post(upload_url, payload)

        return response

    def assert_transcript_upload_response(self, response, expected_status_code, expected_message):
        response_content = json.loads(response.content)
        self.assertEqual(response.status_code, expected_status_code)
        self.assertEqual(response_content['status'], expected_message)

    @ddt.data(
        (u'123-456-789', False),
        (u'', False),
        (u'123-456-789', True)
    )
    @ddt.unpack
    def test_transcript_upload_success(self, edx_video_id, include_bom):
        """
        Tests transcript file upload to video component works as
        expected in case of following:

         1. External video component
         2. VEDA produced video component
         3. Transcript content containing BOM character
        """
        # In case of an external video component, the `edx_video_id` must be empty
        # and VEDA produced video component will have `edx_video_id` set to VAL video ID.
        self.item.edx_video_id = edx_video_id
        modulestore().update_item(self.item, self.user.id)

        # Upload a transcript
        transcript_file = self.bom_srt_file if include_bom else self.good_srt_file
        response = self.upload_transcript(self.video_usage_key, transcript_file)

        # Verify the response
        self.assert_transcript_upload_response(response, expected_status_code=200, expected_message='Success')

        # Verify the `edx_video_id` on the video component
        json_response = json.loads(response.content)
        expected_edx_video_id = edx_video_id if edx_video_id else json_response['edx_video_id']
        video = modulestore().get_item(self.video_usage_key)
        self.assertEqual(video.edx_video_id, expected_edx_video_id)

        # Verify transcript content
        actual_transcript = get_video_transcript_content(video.edx_video_id, language_code=u'en')
        actual_sjson_content = json.loads(actual_transcript['content'])
        expected_sjson_content = json.loads(Transcript.convert(
            self.contents['good'],
            input_format=Transcript.SRT,
            output_format=Transcript.SJSON
        ))
        self.assertDictEqual(actual_sjson_content, expected_sjson_content)

    def test_transcript_upload_without_locator(self):
        """
        Test that transcript upload validation fails if the video locator is missing
        """
        response = self.upload_transcript(locator=None, transcript_file=self.good_srt_file)
        self.assert_transcript_upload_response(
            response,
            expected_status_code=400,
            expected_message=u'Video locator is required.'
        )

    def test_transcript_upload_without_file(self):
        """
        Test that transcript upload validation fails if transcript file is missing
        """
        response = self.upload_transcript(locator=self.video_usage_key, transcript_file=None)
        self.assert_transcript_upload_response(
            response,
            expected_status_code=400,
            expected_message=u'A transcript file is required.'
        )

    def test_transcript_upload_bad_format(self):
        """
        Test that transcript upload validation fails if transcript format is not SRT
        """
        response = self.upload_transcript(locator=self.video_usage_key, transcript_file=self.bad_name_srt_file)
        self.assert_transcript_upload_response(
            response,
            expected_status_code=400,
            expected_message=u'This transcript file type is not supported.'
        )

    def test_transcript_upload_bad_content(self):
        """
        Test that transcript upload validation fails in case of bad transcript content.
        """
        # Request to upload transcript for the video
        response = self.upload_transcript(locator=self.video_usage_key, transcript_file=self.bad_data_srt_file)
        self.assert_transcript_upload_response(
            response,
            expected_status_code=400,
            expected_message=u'There is a problem with this transcript file. Try to upload a different file.'
        )

    def test_transcript_upload_unknown_category(self):
        """
        Test that transcript upload validation fails if item's category is other than video.
        """
        # non_video module setup - i.e. an item whose category is not 'video'.
        data = {
            'parent_locator': unicode(self.course.location),
            'category': 'non_video',
            'type': 'non_video'
        }
        resp = self.client.ajax_post('/xblock/', data)
        usage_key = self._get_usage_key(resp)
        item = modulestore().get_item(usage_key)
        item.data = '<non_video youtube="0.75:JMD_ifUUfsU,1.0:hI10vDNYz4M" />'
        modulestore().update_item(item, self.user.id)

        # Request to upload transcript for the item
        response = self.upload_transcript(locator=usage_key, transcript_file=self.good_srt_file)
        self.assert_transcript_upload_response(
            response,
            expected_status_code=400,
            expected_message=u'Transcripts are supported only for "video" module.'
        )

    def test_transcript_upload_non_existent_item(self):
        """
        Test that transcript upload validation fails in case of invalid item's locator.
        """
        # Request to upload transcript for the item
        response = self.upload_transcript(locator='non_existent_locator', transcript_file=self.good_srt_file)
        self.assert_transcript_upload_response(
            response,
            expected_status_code=400,
            expected_message=u'Cannot find item by locator.'
        )


class TestDownloadTranscripts(BaseTranscripts):
    """
    Tests for '/transcripts/download' url.
    """
    def test_success_download_youtube(self):
        self.item.data = '<video youtube="1:JMD_ifUUfsU" />'
        modulestore().update_item(self.item, self.user.id)

        subs = {
            'start': [100, 200, 240],
            'end': [200, 240, 380],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3'
            ]
        }
        self.save_subs_to_store(subs, 'JMD_ifUUfsU')

        link = reverse('download_transcripts')
        resp = self.client.get(link, {'locator': self.video_usage_key, 'subs_id': "JMD_ifUUfsU"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, """0\n00:00:00,100 --> 00:00:00,200\nsubs #1\n\n1\n00:00:00,200 --> 00:00:00,240\nsubs #2\n\n2\n00:00:00,240 --> 00:00:00,380\nsubs #3\n\n""")

    def test_success_download_nonyoutube(self):
        subs_id = str(uuid4())
        self.item.data = textwrap.dedent("""
            <video youtube="" sub="{}">
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
            </video>
        """.format(subs_id))
        modulestore().update_item(self.item, self.user.id)

        subs = {
            'start': [100, 200, 240],
            'end': [200, 240, 380],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3'
            ]
        }
        self.save_subs_to_store(subs, subs_id)

        link = reverse('download_transcripts')
        resp = self.client.get(link, {'locator': self.video_usage_key, 'subs_id': subs_id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.content,
            '0\n00:00:00,100 --> 00:00:00,200\nsubs #1\n\n1\n00:00:00,200 --> '
            '00:00:00,240\nsubs #2\n\n2\n00:00:00,240 --> 00:00:00,380\nsubs #3\n\n'
        )
        remove_subs_from_store(subs_id, self.item)

    def test_fail_data_without_file(self):
        link = reverse('download_transcripts')
        resp = self.client.get(link, {'locator': ''})
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(link, {})
        self.assertEqual(resp.status_code, 404)

    def test_fail_data_with_bad_locator(self):
        # Test for raising `InvalidLocationError` exception.
        link = reverse('download_transcripts')
        resp = self.client.get(link, {'locator': 'BAD_LOCATOR'})
        self.assertEqual(resp.status_code, 404)

        # Test for raising `ItemNotFoundError` exception.
        link = reverse('download_transcripts')
        resp = self.client.get(link, {'locator': '{0}_{1}'.format(self.video_usage_key, 'BAD_LOCATOR')})
        self.assertEqual(resp.status_code, 404)

    def test_fail_for_non_video_module(self):
        # Video module: setup
        data = {
            'parent_locator': unicode(self.course.location),
            'category': 'videoalpha',
            'type': 'videoalpha'
        }
        resp = self.client.ajax_post('/xblock/', data)
        usage_key = self._get_usage_key(resp)
        subs_id = str(uuid4())
        item = modulestore().get_item(usage_key)
        item.data = textwrap.dedent("""
            <videoalpha youtube="" sub="{}">
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
            </videoalpha>
        """.format(subs_id))
        modulestore().update_item(item, self.user.id)

        subs = {
            'start': [100, 200, 240],
            'end': [200, 240, 380],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3'
            ]
        }
        self.save_subs_to_store(subs, subs_id)

        link = reverse('download_transcripts')
        resp = self.client.get(link, {'locator': unicode(usage_key)})
        self.assertEqual(resp.status_code, 404)

    def test_fail_nonyoutube_subs_dont_exist(self):
        self.item.data = textwrap.dedent("""
            <video youtube="" sub="UNDEFINED">
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
            </video>
        """)
        modulestore().update_item(self.item, self.user.id)

        link = reverse('download_transcripts')
        resp = self.client.get(link, {'locator': self.video_usage_key})
        self.assertEqual(resp.status_code, 404)

    def test_empty_youtube_attr_and_sub_attr(self):
        self.item.data = textwrap.dedent("""
            <video youtube="">
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
            </video>
        """)
        modulestore().update_item(self.item, self.user.id)

        link = reverse('download_transcripts')
        resp = self.client.get(link, {'locator': self.video_usage_key})

        self.assertEqual(resp.status_code, 404)

    def test_fail_bad_sjson_subs(self):
        subs_id = str(uuid4())
        self.item.data = textwrap.dedent("""
            <video youtube="" sub="{}">
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
            </video>
        """.format(subs_id))
        modulestore().update_item(self.item, self.user.id)

        subs = {
            'start': [100, 200, 240],
            'end': [200, 240, 380],
            'text': [
                'subs #1'
            ]
        }
        self.save_subs_to_store(subs, 'JMD_ifUUfsU')

        link = reverse('download_transcripts')
        resp = self.client.get(link, {'locator': self.video_usage_key})

        self.assertEqual(resp.status_code, 404)

    @patch('openedx.core.djangoapps.video_config.models.VideoTranscriptEnabledFlag.feature_enabled', Mock(return_value=True))
    @patch('xmodule.video_module.transcripts_utils.edxval_api.get_video_transcript_data')
    def test_download_fallback_transcript(self, mock_get_video_transcript_data):
        """
        Verify that the val transcript is returned if its not found in content-store.
        """
        mock_get_video_transcript_data.return_value = {
            'content': json.dumps({
                "start": [10],
                "end": [100],
                "text": ["Hi, welcome to Edx."],
            }),
            'file_name': 'edx.sjson'
        }

        self.item.data = textwrap.dedent("""
            <video youtube="" sub="" edx_video_id="123">
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
            </video>
        """)
        modulestore().update_item(self.item, self.user.id)

        download_transcripts_url = reverse('download_transcripts')
        response = self.client.get(download_transcripts_url, {'locator': self.video_usage_key})

        # Expected response
        expected_content = u'0\n00:00:00,010 --> 00:00:00,100\nHi, welcome to Edx.\n\n'
        expected_headers = {
            'content-disposition': 'attachment; filename="edx.srt"',
            'content-type': 'application/x-subrip; charset=utf-8'
        }

        # Assert the actual response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, expected_content)
        for attribute, value in expected_headers.iteritems():
            self.assertEqual(response.get(attribute), value)

    @patch(
        'openedx.core.djangoapps.video_config.models.VideoTranscriptEnabledFlag.feature_enabled',
        Mock(return_value=False),
    )
    def test_download_fallback_transcript_feature_disabled(self):
        """
        Verify the transcript download when feature is disabled.
        """
        self.item.data = textwrap.dedent("""
            <video youtube="" sub="">
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
            </video>
        """)
        modulestore().update_item(self.item, self.user.id)

        download_transcripts_url = reverse('download_transcripts')
        response = self.client.get(download_transcripts_url, {'locator': self.video_usage_key})
        # Assert the actual response
        self.assertEqual(response.status_code, 404)


@ddt.ddt
class TestCheckTranscripts(BaseTranscripts):
    """
    Tests for '/transcripts/check' url.
    """
    def test_success_download_nonyoutube(self):
        subs_id = str(uuid4())
        self.item.data = textwrap.dedent("""
            <video youtube="" sub="{}">
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
            </video>
        """.format(subs_id))
        modulestore().update_item(self.item, self.user.id)

        subs = {
            'start': [100, 200, 240],
            'end': [200, 240, 380],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3'
            ]
        }
        self.save_subs_to_store(subs, subs_id)

        data = {
            'locator': unicode(self.video_usage_key),
            'videos': [{
                'type': 'html5',
                'video': subs_id,
                'mode': 'mp4',
            }]
        }
        link = reverse('check_transcripts')
        resp = self.client.get(link, {'data': json.dumps(data)})
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(
            json.loads(resp.content),
            {
                u'status': u'Success',
                u'youtube_local': False,
                u'is_youtube_mode': False,
                u'youtube_server': False,
                u'command': u'found',
                u'current_item_subs': unicode(subs_id),
                u'youtube_diff': True,
                u'html5_local': [unicode(subs_id)],
                u'html5_equal': False,
            }
        )

        remove_subs_from_store(subs_id, self.item)

    def test_check_youtube(self):
        self.item.data = '<video youtube="1:JMD_ifUUfsU" />'
        modulestore().update_item(self.item, self.user.id)

        subs = {
            'start': [100, 200, 240],
            'end': [200, 240, 380],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3'
            ]
        }
        self.save_subs_to_store(subs, 'JMD_ifUUfsU')
        link = reverse('check_transcripts')
        data = {
            'locator': unicode(self.video_usage_key),
            'videos': [{
                'type': 'youtube',
                'video': 'JMD_ifUUfsU',
                'mode': 'youtube',
            }]
        }

        resp = self.client.get(link, {'data': json.dumps(data)})

        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(
            json.loads(resp.content),
            {
                u'status': u'Success',
                u'youtube_local': True,
                u'is_youtube_mode': True,
                u'youtube_server': False,
                u'command': u'found',
                u'current_item_subs': None,
                u'youtube_diff': True,
                u'html5_local': [],
                u'html5_equal': False,
            }
        )

    @patch('xmodule.video_module.transcripts_utils.requests.get', side_effect=mock_requests_get)
    def test_check_youtube_with_transcript_name(self, mock_get):
        """
        Test that the transcripts are fetched correctly when the the transcript name is set
        """
        self.item.data = '<video youtube="good_id_2" />'
        modulestore().update_item(self.item, self.user.id)

        subs = {
            'start': [100, 200, 240],
            'end': [200, 240, 380],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3'
            ]
        }
        self.save_subs_to_store(subs, 'good_id_2')
        link = reverse('check_transcripts')
        data = {
            'locator': unicode(self.video_usage_key),
            'videos': [{
                'type': 'youtube',
                'video': 'good_id_2',
                'mode': 'youtube',
            }]
        }
        resp = self.client.get(link, {'data': json.dumps(data)})

        mock_get.assert_any_call(
            'http://video.google.com/timedtext',
            params={'lang': 'en', 'v': 'good_id_2', 'name': 'Custom'}
        )

        self.assertEqual(resp.status_code, 200)

        self.assertDictEqual(
            json.loads(resp.content),
            {
                u'status': u'Success',
                u'youtube_local': True,
                u'is_youtube_mode': True,
                u'youtube_server': True,
                u'command': u'replace',
                u'current_item_subs': None,
                u'youtube_diff': True,
                u'html5_local': [],
                u'html5_equal': False,
            }
        )

    def test_fail_data_without_id(self):
        link = reverse('check_transcripts')
        data = {
            'locator': '',
            'videos': [{
                'type': '',
                'video': '',
                'mode': '',
            }]
        }
        resp = self.client.get(link, {'data': json.dumps(data)})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content).get('status'), "Can't find item by locator.")

    def test_fail_data_with_bad_locator(self):
        # Test for raising `InvalidLocationError` exception.
        link = reverse('check_transcripts')
        data = {
            'locator': '',
            'videos': [{
                'type': '',
                'video': '',
                'mode': '',
            }]
        }
        resp = self.client.get(link, {'data': json.dumps(data)})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content).get('status'), "Can't find item by locator.")

        # Test for raising `ItemNotFoundError` exception.
        data = {
            'locator': '{0}_{1}'.format(self.video_usage_key, 'BAD_LOCATOR'),
            'videos': [{
                'type': '',
                'video': '',
                'mode': '',
            }]
        }
        resp = self.client.get(link, {'data': json.dumps(data)})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content).get('status'), "Can't find item by locator.")

    def test_fail_for_non_video_module(self):
        # Not video module: setup
        data = {
            'parent_locator': unicode(self.course.location),
            'category': 'not_video',
            'type': 'not_video'
        }
        resp = self.client.ajax_post('/xblock/', data)
        usage_key = self._get_usage_key(resp)
        subs_id = str(uuid4())
        item = modulestore().get_item(usage_key)
        item.data = textwrap.dedent("""
            <not_video youtube="" sub="{}">
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
            </videoalpha>
        """.format(subs_id))
        modulestore().update_item(item, self.user.id)

        subs = {
            'start': [100, 200, 240],
            'end': [200, 240, 380],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3'
            ]
        }
        self.save_subs_to_store(subs, subs_id)

        data = {
            'locator': unicode(usage_key),
            'videos': [{
                'type': '',
                'video': '',
                'mode': '',
            }]
        }
        link = reverse('check_transcripts')
        resp = self.client.get(link, {'data': json.dumps(data)})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content).get('status'), 'Transcripts are supported only for "video" modules.')

    @patch('xmodule.video_module.transcripts_utils.get_video_transcript_content')
    def test_command_for_fallback_transcript(self, mock_get_video_transcript_content):
        """
        Verify the command if a transcript is there in edx-val.
        """
        mock_get_video_transcript_content.return_value = {
            'content': json.dumps({
                "start": [10],
                "end": [100],
                "text": ["Hi, welcome to Edx."],
            }),
            'file_name': 'edx.sjson'
        }

        # video_transcript_feature.return_value = feature_enabled
        self.item.data = textwrap.dedent("""
            <video youtube="" sub="" edx_video_id="123">
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
                <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
            </video>
        """)
        modulestore().update_item(self.item, self.user.id)

        # Make request to check transcript view
        data = {
            'locator': unicode(self.video_usage_key),
            'videos': [{
                'type': 'html5',
                'video': "",
                'mode': 'mp4',
            }]
        }
        check_transcripts_url = reverse('check_transcripts')
        response = self.client.get(check_transcripts_url, {'data': json.dumps(data)})

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            json.loads(response.content),
            {
                u'status': u'Success',
                u'youtube_local': False,
                u'is_youtube_mode': False,
                u'youtube_server': False,
                u'command': 'found',
                u'current_item_subs': None,
                u'youtube_diff': True,
                u'html5_local': [],
                u'html5_equal': False,
            }
        )
