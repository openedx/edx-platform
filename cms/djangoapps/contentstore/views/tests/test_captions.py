"""Tests for items views."""

import json
from uuid import uuid4
import copy
import textwrap
from pymongo import MongoClient

from django.test.utils import override_settings
from django.conf import settings

from xmodule.video_module import transcripts_utils
from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url
from contentstore.views.utilities.captions import get_videos
from cache_toolbox.core import del_cached_content
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore, _CONTENTSTORE
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError
from opaque_keys.edx.keys import UsageKey

#from contentstore.tests.modulestore_config import TEST_MODULESTORE


TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


#@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE, MODULESTORE=TEST_MODULESTORE)
@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class Basetranscripts(CourseTestCase):
    """Base test class for transcripts tests."""

    org = 'MITx'
    number = '999'

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

    def setUp(self):
        """Create initial data."""
        super(Basetranscripts, self).setUp()
        self.location = self.course.id.make_usage_key('course', self.course.id.run)
        self.captions_url = reverse_course_url('utility_captions_handler', self.course.id)
        self.unicode_locator = unicode(self.location)

        # Add video module
        data = {
            # 'parent_locator': self.location.to_deprecated_string(),
            'parent_locator': self.unicode_locator,
            'category': 'video',
            'type': 'video'
        }
        resp = self.client.ajax_post('http://testserver/xblock/', data)
        videos = get_videos(self.course)

        self.item_location = self._get_locator(resp)
        self.item_location_string = str(self.item_location)
        self.assertEqual(resp.status_code, 200)

        self.item = modulestore().get_item(self.item_location)
        # hI10vDNYz4M - valid Youtube ID with transcripts.
        # JMD_ifUUfsU, AKqURZnYqpk, DYpADpL7jAY - valid Youtube IDs without transcripts.
        self.item.data = '<video youtube="0.75:JMD_ifUUfsU,1.0:hI10vDNYz4M,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" />'
        modulestore().update_item(self.item, self.user.id)

        self.item = modulestore().get_item(self.item_location)
        # Remove all transcripts for current module.
        self.clear_subs_content()

    def _get_locator(self, resp):
        """ Returns the locator and old-style location (as a string) from the response returned by a create operation. """
        locator_string = json.loads(resp.content).get('locator')
        locator = UsageKey.from_string(locator_string)
        # locator = self.course.id.make_usage_key('course', locator_string)
        return locator

    def get_youtube_ids(self):
        """Return youtube speeds and ids."""
        item = modulestore().get_item(self.item_location)

        return {
            0.75: item.youtube_id_0_75,
            1: item.youtube_id_1_0,
            1.25: item.youtube_id_1_25,
            1.5: item.youtube_id_1_5
        }

    def tearDown(self):
        modulestore()._drop_database()
        _CONTENTSTORE.clear()


class TestCheckcaptions(Basetranscripts):
    """Tests for '/utility/captions' url."""

    def save_subs_to_store(self, subs, subs_id):
        """Save transcripts into `StaticContent`."""
        filedata = json.dumps(subs, indent=2)
        mime_type = 'application/json'
        filename = 'subs_{0}.srt.sjson'.format(subs_id)

        content_location = StaticContent.compute_location(self.course.id, filename)
        content = StaticContent(content_location, filename, mime_type, filedata)
        contentstore().save(content)
        del_cached_content(content_location)
        return content_location

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

        link = self.captions_url
        data = {
            'video': json.dumps({'location': self.item_location_string}),
        }
        resp = self.client.get(link, data, HTTP_ACCEPT='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(
            json.loads(resp.content),
            {
                u'status': True,
                u'location': self.item_location_string,
                u'command': u'use_existing',
                u'current_item_subs': subs_id,
                u'html5_equal': False,
                u'html5_local': [],
                u'is_youtube_mode': False,
                u'status': u'Success',
                u'subs': u'',
                u'youtube_diff': True,
                u'youtube_local': False,
                u'youtube_server': False
            }
        )

        transcripts_utils.remove_subs_from_store(subs_id, self.item)

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
        link = self.captions_url
        data = {
            'video': json.dumps({'location': self.item_location_string}),
        }
        resp = self.client.get(link, data, HTTP_ACCEPT='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(
            json.loads(resp.content),
            {
                u'command': u'found',
                u'current_item_subs': None,
                u'html5_equal': False,
                u'html5_local': [],
                u'is_youtube_mode': True,
                u'status': u'Success',
                u'subs': u'JMD_ifUUfsU',
                u'youtube_diff': True,
                u'youtube_local': True,
                u'youtube_server': False,
                u'location': self.item_location_string,
            }
        )

    def test_fail_data_without_id(self):
        link = self.captions_url
        data = {
            'video': '',
        }
        resp = self.client.get(link, data, HTTP_ACCEPT='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content).get('message'), "Invalid location.")

    def test_fail_data_with_bad_locator(self):
        # Test for raising `InvalidKeyError` exception.
        link = self.captions_url
        data = {
            'video': json.dumps({
                'location': '',
            }),
        }
        resp = self.client.get(link, data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content).get('message'), "Can't find item by locator.")

        # Test for raising `ItemNotFoundError` exception.
        data = {
            'video': json.dumps({
                'location': '{0}_{1}'.format(self.item_location_string, 'BAD_LOCATION')
            }),
        }
        resp = self.client.get(link, data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content).get('message'), "Can't find item by locator.")

    def test_fail_for_non_video_module(self):
        # Not video module: setup
        data = {
            'parent_locator': self.unicode_locator,
            'category': 'not_video',
            'type': 'not_video'
        }
        resp = self.client.ajax_post('http://testserver/xblock/', data)
        item_location = self._get_locator(resp)
        item_location_string = str(item_location)
        subs_id = str(uuid4())
        item = modulestore().get_item(item_location)
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

        link = self.captions_url
        data = {
            'video': json.dumps({'location': item_location_string}),
        }
        resp = self.client.get(link, data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content).get('message'), 'Transcripts are supported only for "video" modules.')
