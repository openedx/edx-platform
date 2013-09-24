"""Tests for items views."""

import os
import json
import tempfile
from uuid import uuid4
import copy
from pymongo import MongoClient

from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.test.utils import override_settings
from django.conf import settings

from contentstore import transcripts_utils
from contentstore.tests.utils import CourseTestCase
from cache_toolbox.core import del_cached_content
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore, _CONTENTSTORE
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError

from contentstore.tests.modulestore_config import TEST_MODULESTORE
TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['OPTIONS']['db'] = 'test_xcontent_%s' % uuid4().hex


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE, MODULESTORE=TEST_MODULESTORE)
class Basetranscripts(CourseTestCase):
    """Base test class for transcripts tests."""

    org = 'MITx'
    number = '999'

    def clear_subs_content(self):
        """Remove, if transcripts content exists."""
        for youtube_id in self.get_youtube_ids().values():
            filename = 'subs_{0}.srt.sjson'.format(youtube_id)
            content_location = StaticContent.compute_location(
                self.org, self.number, filename)
            try:
                content = contentstore().find(content_location)
                contentstore().delete(content.get_id())
            except NotFoundError:
                pass

    def setUp(self):
        """Create initial data."""
        super(Basetranscripts, self).setUp()

        # Add video module
        data = {
            'parent_location': str(self.course_location),
            'category': 'video',
            'type': 'video'
        }
        resp = self.client.post(reverse('create_item'), data)
        self.item_location = json.loads(resp.content).get('id')
        self.assertEqual(resp.status_code, 200)

        # hI10vDNYz4M - valid Youtube ID with transcripts.
        # JMD_ifUUfsU, AKqURZnYqpk, DYpADpL7jAY - valid Youtube IDs
        # without transcripts.
        data = '<video youtube="0.75:JMD_ifUUfsU,1.0:hI10vDNYz4M,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" />'
        modulestore().update_item(self.item_location, data)

        self.item = modulestore().get_item(self.item_location)

        # Remove all transcripts for current module.
        self.clear_subs_content()

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
        MongoClient().drop_database(TEST_DATA_CONTENTSTORE['OPTIONS']['db'])
        _CONTENTSTORE.clear()


class TestUploadtranscripts(Basetranscripts):
    """Tests for '/process_transcripts/upload' url."""

    def setUp(self):
        """Create initial data."""
        super(TestUploadtranscripts, self).setUp()

        self.good_srt_file = tempfile.NamedTemporaryFile(suffix='.srt')
        self.good_srt_file.write("""
1
00:00:10,500 --> 00:00:13,000
Elephant's Dream

2
00:00:15,000 --> 00:00:18,000
At the left we can see...
        """)
        self.good_srt_file.seek(0)

        self.bad_data_srt_file = tempfile.NamedTemporaryFile(suffix='.srt')
        self.bad_data_srt_file.write('Some BAD data')
        self.bad_data_srt_file.seek(0)

        self.bad_name_srt_file = tempfile.NamedTemporaryFile(suffix='.BAD')
        self.bad_name_srt_file.write("""
1
00:00:10,500 --> 00:00:13,000
Elephant's Dream

2
00:00:15,000 --> 00:00:18,000
At the left we can see...
        """)
        self.bad_name_srt_file.seek(0)

    def test_success_video_module_source_subs_uploading(self):
        data = """
<video youtube="">
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
</video>
"""
        modulestore().update_item(self.item_location, data)

        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'id': self.item_location, 'file': self.good_srt_file})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Success')

        filename = slugify(
            os.path.splitext(os.path.basename(self.good_srt_file.name))[0])
        item = modulestore().get_item(self.item_location)
        self.assertEqual(item.sub, filename)

        content_location = StaticContent.compute_location(
            self.org, self.number, 'subs_{0}.srt.sjson'.format(filename))
        self.assertTrue(contentstore().find(content_location))

    def test_fail_data_without_id(self):
        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'file': self.good_srt_file})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

    def test_fail_data_without_file(self):
        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'id': self.item_location})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

    def test_fail_data_with_bad_location(self):
        # Test for raising `InvalidLocationError` exception.
        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'id': 'BAD_LOCATION', 'file': self.good_srt_file})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

        # Test for raising `ItemNotFoundError` exception.
        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'id': '{0}_{1}'.format(self.item_location, 'BAD_LOCATION'), 'file': self.good_srt_file})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

    def test_fail_for_non_video_module(self):
        # Videoalpha module: setup
        data = {
            'parent_location': str(self.course_location),
            'category': 'videoalpha',
            'type': 'videoalpha'
        }
        resp = self.client.post(reverse('create_item'), data)
        item_location = json.loads(resp.content).get('id')
        data = '<videoalpha youtube="0.75:JMD_ifUUfsU,1.0:hI10vDNYz4M" />'
        modulestore().update_item(item_location, data)

        # Videoalpha module: testing

        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'id': item_location, 'file': self.good_srt_file})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

    def test_fail_bad_xml(self):
        data = '<<<video youtube="0.75:JMD_ifUUfsU,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" />'
        modulestore().update_item(self.item_location, data)

        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'id': self.item_location, 'file': self.good_srt_file})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

    def test_fail_miss_youtube_and_source_attrs(self):
        data = """
<video youtube="">
    <source src=""/>
</video>
"""
        modulestore().update_item(self.item_location, data)

        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'id': self.item_location, 'file': self.good_srt_file})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

        data = '<video />'
        modulestore().update_item(self.item_location, data)

        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'id': self.item_location, 'file': self.good_srt_file})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

    def test_fail_bad_data_srt_file(self):

        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'id': self.item_location, 'file': self.bad_data_srt_file})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

    def test_fail_bad_name_srt_file(self):
        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'id': self.item_location, 'file': self.bad_data_srt_file})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

    def test_undefined_file_extension(self):
        srt_file = tempfile.NamedTemporaryFile(suffix='')
        srt_file.write("""
1
00:00:10,500 --> 00:00:13,000
Elephant's Dream

2
00:00:15,000 --> 00:00:18,000
At the left we can see...
        """)
        srt_file.seek(0)

        link = reverse('process_transcripts', args=('upload',))
        resp = self.client.post(link, {'id': self.item_location, 'file': srt_file})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

    def tearDown(self):
        super(TestUploadtranscripts, self).tearDown()

        self.good_srt_file.close()
        self.bad_data_srt_file.close()
        self.bad_name_srt_file.close()


class TestDownloadtranscripts(Basetranscripts):
    """Tests for '/process_transcripts/download' url."""

    def save_subs_to_store(self, subs, subs_id):
        """Save transcripts into `StaticContent`."""
        filedata = json.dumps(subs, indent=2)
        mime_type = 'application/json'
        filename = 'subs_{0}.srt.sjson'.format(subs_id)

        content_location = StaticContent.compute_location(
            self.org, self.number, filename)
        content = StaticContent(content_location, filename, mime_type, filedata)
        contentstore().save(content)
        del_cached_content(content_location)
        return content_location

    def remove_subs_from_store(self, subs_id):
        """Remove from store, if transcripts content exists."""
        filename = 'subs_{0}.srt.sjson'.format(subs_id)
        content_location = StaticContent.compute_location(
            self.org, self.number, filename)
        try:
            content = contentstore().find(content_location)
            contentstore().delete(content.get_id())
        except NotFoundError:
            pass

    def test_success_download_youtube(self):
        data = '<video youtube="1:JMD_ifUUfsU" />'
        modulestore().update_item(self.item_location, data)

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

        link = reverse('process_transcripts', args=('download',))
        resp = self.client.get(link, {'id': self.item_location})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, """0\n00:00:00,100 --> 00:00:00,200\nsubs #1\n\n1\n00:00:00,200 --> 00:00:00,240\nsubs #2\n\n2\n00:00:00,240 --> 00:00:00,380\nsubs #3\n\n""")

    def test_success_download_nonyoutube(self):
        subs_id = str(uuid4())
        data = """
<video youtube="" sub="{}">
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
</video>
""".format(subs_id)
        modulestore().update_item(self.item_location, data)

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

        link = reverse('process_transcripts', args=('download',))
        resp = self.client.get(link, {'id': self.item_location})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.content,
            '0\n00:00:00,100 --> 00:00:00,200\nsubs #1\n\n1\n00:00:00,200 --> \
00:00:00,240\nsubs #2\n\n2\n00:00:00,240 --> 00:00:00,380\nsubs #3\n\n')
        transcripts_utils.remove_subs_from_store(subs_id, self.item)

    def test_fail_data_without_file(self):
        link = reverse('process_transcripts', args=('download',))
        resp = self.client.get(link, {'id': ''})
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(link, {})
        self.assertEqual(resp.status_code, 404)

    def test_fail_data_with_bad_location(self):
        # Test for raising `InvalidLocationError` exception.
        link = reverse('process_transcripts', args=('download',))
        resp = self.client.get(link, {'id': 'BAD_LOCATION'})
        self.assertEqual(resp.status_code, 404)

        # Test for raising `ItemNotFoundError` exception.
        link = reverse('process_transcripts', args=('download',))
        resp = self.client.get(link, {'id': '{0}_{1}'.format(self.item_location, 'BAD_LOCATION')})
        self.assertEqual(resp.status_code, 404)

    def test_fail_for_non_video_module(self):
        # Video module: setup
        data = {
            'parent_location': str(self.course_location),
            'category': 'videoalpha',
            'type': 'videoalpha'
        }
        resp = self.client.post(reverse('create_item'), data)
        item_location = json.loads(resp.content).get('id')
        subs_id = str(uuid4())
        data = """
<videoalpha youtube="" sub="{}">
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
</videoalpha>
""".format(subs_id)
        modulestore().update_item(item_location, data)

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

        link = reverse('process_transcripts', args=('download',))
        resp = self.client.get(link, {'id': item_location})
        self.assertEqual(resp.status_code, 404)

    def test_fail_nonyoutube_subs_dont_exist(self):
        data = """
<video youtube="" sub="UNDEFINED">
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
</video>
"""
        modulestore().update_item(self.item_location, data)

        link = reverse('process_transcripts', args=('download',))
        resp = self.client.get(link, {'id': self.item_location})
        self.assertEqual(resp.status_code, 404)

    def test_empty_youtube_attr_and_sub_attr(self):
        data = """
<video youtube="">
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
</video>
"""
        modulestore().update_item(self.item_location, data)

        link = reverse('process_transcripts', args=('download',))
        resp = self.client.get(link, {'id': self.item_location})

        self.assertEqual(resp.status_code, 404)

    def test_fail_bad_sjson_subs(self):
        subs_id = str(uuid4())
        data = """
<video youtube="" sub="{}">
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
</video>
""".format(subs_id)
        modulestore().update_item(self.item_location, data)

        subs = {
            'start': [100, 200, 240],
            'end': [200, 240, 380],
            'text': [
                'subs #1'
            ]
        }
        self.save_subs_to_store(subs, 'JMD_ifUUfsU')

        link = reverse('process_transcripts', args=('download',))
        resp = self.client.get(link, {'id': self.item_location})

        self.assertEqual(resp.status_code, 404)


class TestChecktranscripts(Basetranscripts):
    """Tests for '/process_transcripts/check' url."""

    def save_subs_to_store(self, subs, subs_id):
        """Save transcripts into `StaticContent`."""
        filedata = json.dumps(subs, indent=2)
        mime_type = 'application/json'
        filename = 'subs_{0}.srt.sjson'.format(subs_id)

        content_location = StaticContent.compute_location(
            self.org, self.number, filename)
        content = StaticContent(content_location, filename, mime_type, filedata)
        contentstore().save(content)
        del_cached_content(content_location)
        return content_location

    def remove_subs_from_store(self, subs_id):
        """Remove from store, if transcripts content exists."""
        filename = 'subs_{0}.srt.sjson'.format(subs_id)
        content_location = StaticContent.compute_location(
            self.org, self.number, filename)
        try:
            content = contentstore().find(content_location)
            contentstore().delete(content.get_id())
        except NotFoundError:
            pass

    def test_success_download_nonyoutube(self):
        subs_id = str(uuid4())
        data = """
<video youtube="" sub="{}">
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
</video>
""".format(subs_id)
        modulestore().update_item(self.item_location, data)

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
            'id':  self.item_location,
            'videos': [{
                'type': 'html5',
                'video': subs_id,
                'mode': 'mp4',
            }]
        }
        link = reverse('process_transcripts', args=('check',))
        resp = self.client.get(link, {'data': json.dumps(data)})
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(
            json.loads(resp.content),
            {
                u'status': u'Success',
                u'subs': unicode(subs_id),
                u'youtube_local': False,
                u'is_youtube_mode': False,
                u'youtube_server': False,
                u'command': u'found',
                u'current_item_subs': unicode(subs_id),
                u'youtube_diff': True,
                u'html5_local': [unicode(subs_id)]
            }
        )

        transcripts_utils.remove_subs_from_store(subs_id, self.item)

    def test_check_youtube(self):
        data = '<video youtube="1:JMD_ifUUfsU" />'
        modulestore().update_item(self.item_location, data)

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
        link = reverse('process_transcripts', args=('check',))
        data = {
            'id': self.item_location,
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
                u'subs': u'JMD_ifUUfsU',
                u'youtube_local': True,
                u'is_youtube_mode': True,
                u'youtube_server': False,
                u'command': u'found',
                u'current_item_subs': u'',
                u'youtube_diff': True,
                u'html5_local': []
            }
        )

    def test_fail_data_without_file(self):
        link = reverse('process_transcripts', args=('check',))
        data = {
            'id': '',
            'videos': [{
                'type': '',
                'video': '',
                'mode': '',
            }]
        }
        resp = self.client.get(link, {'data': json.dumps(data)})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

    def test_fail_data_with_bad_location(self):
        # Test for raising `InvalidLocationError` exception.
        link = reverse('process_transcripts', args=('check',))
        data = {
            'id': '',
            'videos': [{
                'type': '',
                'video': '',
                'mode': '',
            }]
        }
        resp = self.client.get(link, {'data': json.dumps(data)})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

        # Test for raising `ItemNotFoundError` exception.
        data = {
            'id':  '{0}_{1}'.format(self.item_location, 'BAD_LOCATION'),
            'videos': [{
                'type': '',
                'video': '',
                'mode': '',
            }]
        }
        resp = self.client.get(link, {'data': json.dumps(data)})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

    def test_fail_for_non_video_module(self):
        # Not video module: setup
        data = {
            'parent_location': str(self.course_location),
            'category': 'not_video',
            'type': 'not_video'
        }
        resp = self.client.post(reverse('create_item'), data)
        item_location = json.loads(resp.content).get('id')
        subs_id = str(uuid4())
        data = """
<not_video youtube="" sub="{}">
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
</videoalpha>
""".format(subs_id)
        modulestore().update_item(item_location, data)

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
            'id':  item_location,
            'videos': [{
                'type': '',
                'video': '',
                'mode': '',
            }]
        }
        link = reverse('process_transcripts', args=('check',))
        resp = self.client.get(link, {'data': json.dumps(data)})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content).get('status'), 'Error')

