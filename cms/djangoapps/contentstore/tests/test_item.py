"""Tests for items views."""
import os
import json
import tempfile

from lxml import etree
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from contentstore.tests.test_course_settings import CourseTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError


class DeleteItem(CourseTestCase):
    """Tests for '/delete_item' url."""
    def setUp(self):
        """ Creates the test course with a static page in it. """
        super(DeleteItem, self).setUp()
        self.course = CourseFactory.create(org='mitX', number='333', display_name='Dummy Course')

    def test_delete_static_page(self):
        # Add static tab
        data = {
            'parent_location': 'i4x://mitX/333/course/Dummy_Course',
            'template': 'i4x://edx/templates/static_tab/Empty'
        }

        resp = self.client.post(reverse('clone_item'), data)
        self.assertEqual(resp.status_code, 200)

        # Now delete it. There was a bug that the delete was failing (static tabs do not exist in draft modulestore).
        resp = self.client.post(reverse('delete_item'), resp.content, "application/json")
        self.assertEqual(resp.status_code, 200)


class BaseSubtitles(CourseTestCase):
    """Base test class for subtitles tests."""

    org = 'MITx'
    number = '999'

    def clear_subs_content(self):
        """Remove, if subtitles content exists."""
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
        super(BaseSubtitles, self).setUp()

        # Add videoalpha module
        data = {
            'parent_location': str(self.course_location),
            'template': 'i4x://edx/templates/videoalpha/Video_Alpha'
        }
        resp = self.client.post(reverse('clone_item'), data)
        self.item_location = json.loads(resp.content).get('id')
        self.assertEqual(resp.status_code, 200)

        # hI10vDNYz4M - valid Youtube ID with subtitles.
        # JMD_ifUUfsU, AKqURZnYqpk, DYpADpL7jAY - valid Youtube IDs
        # without subtitles.
        data = '<videoalpha youtube="0.75:JMD_ifUUfsU,1.0:hI10vDNYz4M,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" />'
        modulestore().update_item(self.item_location, data)

        self.item = modulestore().get_item(self.item_location)

        # Remove all subtitles for current module.
        self.clear_subs_content()

    def get_youtube_ids(self):
        """Return youtube speeds and ids."""
        xmltree = etree.fromstring(self.item.data)
        youtube = xmltree.get('youtube')
        return dict([
            (float(i.split(':')[0]), i.split(':')[1])
            for i in youtube.split(',')
        ])


class ImportSubtitles(BaseSubtitles):
    """Tests for '/import_subtitles' url."""

    def test_success_videoalpha_module_subs_importing(self):
        # Import subtitles.
        resp = self.client.post(
            reverse('import_subtitles'), {'id': self.item_location})

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content).get('success'))

        # Check assets status after importing subtitles.
        for youtube_id in self.get_youtube_ids().values():
            filename = 'subs_{0}.srt.sjson'.format(youtube_id)
            content_location = StaticContent.compute_location(
                self.org, self.number, filename)
            self.assertTrue(contentstore().find(content_location))

    def test_fail_data_without_id(self):
        resp = self.client.post(
            reverse('import_subtitles'), {})

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_data_with_bad_location(self):
        # Test for raising `InvalidLocationError` exception.
        resp = self.client.post(
            reverse('import_subtitles'), {'id': 'BAD_LOCATION'})

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

        # Test for raising `ItemNotFoundError` exception.
        resp = self.client.post(
            reverse('import_subtitles'),
            {'id': '{0}_{1}'.format(self.item_location, 'BAD_LOCATION')}
        )

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_for_non_videoalpha_module(self):
        # Video module: setup
        data = {
            'parent_location': str(self.course_location),
            'template': 'i4x://edx/templates/video/default'
        }
        resp = self.client.post(reverse('clone_item'), data)
        item_location = json.loads(resp.content).get('id')
        data = '<video youtube="0.75:JMD_ifUUfsU,1.0:hI10vDNYz4M,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" />'
        modulestore().update_item(item_location, data)

        # Video module: testing
        resp = self.client.post(
            reverse('import_subtitles'), {'id': item_location})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_bad_xml(self):
        data = '<<<videoalpha youtube="0.75:JMD_ifUUfsU,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" />'
        modulestore().update_item(self.item_location, data)

        # Import subtitles.
        resp = self.client.post(
            reverse('import_subtitles'), {'id': self.item_location})

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_miss_youtube_attr(self):
        data = '<videoalpha youtube="" />'
        modulestore().update_item(self.item_location, data)

        # Import subtitles.
        resp = self.client.post(
            reverse('import_subtitles'), {'id': self.item_location})

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

        data = '<videoalpha />'
        modulestore().update_item(self.item_location, data)

        # Import subtitles.
        resp = self.client.post(
            reverse('import_subtitles'), {'id': self.item_location})

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_bad_youtube_attr(self):
        data = '<videoalpha youtube=":JMD_ifUUfsU,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" />'
        modulestore().update_item(self.item_location, data)

        # Import subtitles.
        resp = self.client.post(
            reverse('import_subtitles'), {'id': self.item_location})

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_youtube_ids_unavailable(self):
        data = '<videoalpha youtube="0.75:BAD_YOUTUBE_ID1,1.25:BAD_YOUTUBE_ID2,1.50:BAD_YOUTUBE_ID3" />'
        modulestore().update_item(self.item_location, data)

        # Import subtitles.
        resp = self.client.post(
            reverse('import_subtitles'), {'id': self.item_location})

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def tearDown(self):
        super(ImportSubtitles, self).tearDown()

        # Remove all subtitles for current module.
        self.clear_subs_content()


class UploadSubtitles(BaseSubtitles):
    """Tests for '/upload_subtitles' url."""

    def setUp(self):
        """Create initial data."""
        super(UploadSubtitles, self).setUp()

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

    def test_success_videoalpha_module_youtube_subs_uploading(self):
        # Check assets status before uploading subtitles.
        for youtube_id in self.get_youtube_ids().values():
            filename = 'subs_{0}.srt.sjson'.format(youtube_id)
            content_location = StaticContent.compute_location(
                self.org, self.number, filename)
            self.assertRaises(
                NotFoundError, contentstore().find, content_location)

        resp = self.client.post(
            reverse('upload_subtitles'),
            {
                'id': self.item_location,
                'file': self.good_srt_file
            })

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content).get('success'))

        # Check assets status after uploading subtitles.
        for youtube_id in self.get_youtube_ids().values():
            filename = 'subs_{0}.srt.sjson'.format(youtube_id)
            content_location = StaticContent.compute_location(
                self.org, self.number, filename)
            self.assertTrue(contentstore().find(content_location))

    def test_success_videoalpha_module_source_subs_uploading(self):
        data = """
<videoalpha youtube="">
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.mp4"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.webm"/>
    <source src="http://www.quirksmode.org/html5/videos/big_buck_bunny.ogv"/>
</videoalpha>
"""
        modulestore().update_item(self.item_location, data)

        resp = self.client.post(
            reverse('upload_subtitles'),
            {
                'id': self.item_location,
                'file': self.good_srt_file
            })

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content).get('success'))
        self.assertTrue(json.loads(resp.content).get('xml'))

        filename = slugify(
            os.path.splitext(os.path.basename(self.good_srt_file.name))[0])
        item = modulestore().get_item(self.item_location)
        self.assertEqual(
            etree.fromstring(item.data).get('sub'),
            filename)

        content_location = StaticContent.compute_location(
            self.org, self.number, 'subs_{0}.srt.sjson'.format(filename))
        self.assertTrue(contentstore().find(content_location))

    def test_fail_data_without_id(self):
        resp = self.client.post(
            reverse('upload_subtitles'), {'file': self.good_srt_file})

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_data_without_file(self):
        resp = self.client.post(
            reverse('upload_subtitles'), {'id': self.item_location})

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_data_with_bad_location(self):
        # Test for raising `InvalidLocationError` exception.
        resp = self.client.post(
            reverse('import_subtitles'),
            {
                'id': 'BAD_LOCATION',
                'file': self.good_srt_file
            })

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

        # Test for raising `ItemNotFoundError` exception.
        resp = self.client.post(
            reverse('upload_subtitles'),
            {
                'id': '{0}_{1}'.format(self.item_location, 'BAD_LOCATION'),
                'file': self.good_srt_file
            })

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_for_non_videoalpha_module(self):
        # Video module: setup
        data = {
            'parent_location': str(self.course_location),
            'template': 'i4x://edx/templates/video/default'
        }
        resp = self.client.post(reverse('clone_item'), data)
        item_location = json.loads(resp.content).get('id')
        data = '<video youtube="0.75:JMD_ifUUfsU,1.0:hI10vDNYz4M" />'
        modulestore().update_item(item_location, data)

        # Video module: testing
        resp = self.client.post(
            reverse('upload_subtitles'),
            {
                'id': item_location,
                'file': self.good_srt_file
            })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_bad_xml(self):
        data = '<<<videoalpha youtube="0.75:JMD_ifUUfsU,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" />'
        modulestore().update_item(self.item_location, data)

        resp = self.client.post(
            reverse('upload_subtitles'),
            {
                'id': self.item_location,
                'file': self.good_srt_file
            })

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_bad_youtube_attr(self):
        data = '<videoalpha youtube=":JMD_ifUUfsU,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" />'
        modulestore().update_item(self.item_location, data)

        resp = self.client.post(
            reverse('upload_subtitles'),
            {
                'id': self.item_location,
                'file': self.good_srt_file
            })

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_miss_youtube_and_source_attrs(self):
        data = '<videoalpha youtube="" />'
        modulestore().update_item(self.item_location, data)

        resp = self.client.post(
            reverse('upload_subtitles'),
            {
                'id': self.item_location,
                'file': self.good_srt_file
            })

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

        data = '<videoalpha />'
        modulestore().update_item(self.item_location, data)

        resp = self.client.post(
            reverse('upload_subtitles'),
            {
                'id': self.item_location,
                'file': self.good_srt_file
            })

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_bad_data_srt_file(self):
        resp = self.client.post(
            reverse('upload_subtitles'),
            {
                'id': self.item_location,
                'file': self.bad_data_srt_file
            })

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def test_fail_bad_name_srt_file(self):
        resp = self.client.post(
            reverse('upload_subtitles'),
            {
                'id': self.item_location,
                'file': self.bad_name_srt_file
            })

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

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

        resp = self.client.post(
            reverse('upload_subtitles'),
            {
                'id': self.item_location,
                'file': srt_file
            })

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content).get('success'))

    def tearDown(self):
        super(UploadSubtitles, self).tearDown()

        self.good_srt_file.close()
        self.bad_data_srt_file.close()
        self.bad_name_srt_file.close()
