"""
Unit tests for the asset upload endpoint.
"""

#pylint: disable=C0111
#pylint: disable=W0621
#pylint: disable=W0212

from datetime import datetime, timedelta
from io import BytesIO
from pytz import UTC
import json
import re
from unittest import TestCase, skip
from .utils import CourseTestCase
from contentstore.views import assets
from xmodule.contentstore.content import StaticContent, XASSET_LOCATION_TAG
from xmodule.modulestore import Location
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.mongo.base import location_to_query


class AssetsTestCase(CourseTestCase):
    def setUp(self):
        super(AssetsTestCase, self).setUp()
        location = loc_mapper().translate_location(self.course.location.course_id, self.course.location, False, True)
        self.url = location.url_reverse('assets/', '')

    def test_basic(self):
        resp = self.client.get(self.url, HTTP_ACCEPT='text/html')
        self.assertEquals(resp.status_code, 200)

    def test_static_url_generation(self):
        location = Location(['i4x', 'foo', 'bar', 'asset', 'my_file_name.jpg'])
        path = StaticContent.get_static_path_from_location(location)
        self.assertEquals(path, '/static/my_file_name.jpg')


class AssetsToyCourseTestCase(CourseTestCase):
    """
    Tests the assets returned from assets_handler for the toy test course.
    """
    def test_toy_assets(self):
        module_store = modulestore('direct')
        _, course_items = import_from_xml(
            module_store,
            'common/test/data/',
            ['toy'],
            static_content_store=contentstore(),
            verbose=True
        )
        course = course_items[0]
        location = loc_mapper().translate_location(course.location.course_id, course.location, False, True)
        url = location.url_reverse('assets/', '')

        self.assert_correct_asset_response(url, 0, 3, 3)
        self.assert_correct_asset_response(url + '?page_size=2', 0, 2, 3)
        self.assert_correct_asset_response(url + '?page_size=2&page=1', 2, 1, 3)
        self.assert_correct_sort_response(url, 'date_added', 'asc')
        self.assert_correct_sort_response(url, 'date_added', 'desc')
        self.assert_correct_sort_response(url, 'display_name', 'asc')
        self.assert_correct_sort_response(url, 'display_name', 'desc')

    def assert_correct_asset_response(self, url, expected_start, expected_length, expected_total):
        resp = self.client.get(url, HTTP_ACCEPT='application/json')
        json_response = json.loads(resp.content)
        assets = json_response['assets']
        self.assertEquals(json_response['start'], expected_start)
        self.assertEquals(len(assets), expected_length)
        self.assertEquals(json_response['totalCount'], expected_total)

    def assert_correct_sort_response(self, url, sort, direction):
        resp = self.client.get(url + '?sort=' + sort + '&direction=' + direction, HTTP_ACCEPT='application/json')
        json_response = json.loads(resp.content)
        assets = json_response['assets']
        name1 = assets[0][sort]
        name2 = assets[1][sort]
        name3 = assets[2][sort]
        if direction == 'asc':
            self.assertLessEqual(name1, name2)
            self.assertLessEqual(name2, name3)
        else:
            self.assertGreaterEqual(name1, name2)
            self.assertGreaterEqual(name2, name3)


class UploadTestCase(CourseTestCase):
    """
    Unit tests for uploading a file
    """
    def setUp(self):
        super(UploadTestCase, self).setUp()
        location = loc_mapper().translate_location(self.course.location.course_id, self.course.location, False, True)
        self.url = location.url_reverse('assets/', '')

    @skip("CorruptGridFile error on continuous integration server")
    def test_happy_path(self):
        f = BytesIO("sample content")
        f.name = "sample.txt"
        resp = self.client.post(self.url, {"name": "my-name", "file": f})
        self.assertEquals(resp.status_code, 200)

    def test_no_file(self):
        resp = self.client.post(self.url, {"name": "file.txt"}, "application/json")
        self.assertEquals(resp.status_code, 400)


class AssetToJsonTestCase(TestCase):
    """
    Unit test for transforming asset information into something
    we can send out to the client via JSON.
    """
    def test_basic(self):
        upload_date = datetime(2013, 6, 1, 10, 30, tzinfo=UTC)

        location = Location(['i4x', 'foo', 'bar', 'asset', 'my_file_name.jpg'])
        thumbnail_location = Location(['i4x', 'foo', 'bar', 'asset', 'my_file_name_thumb.jpg'])

        output = assets._get_asset_json("my_file", upload_date, location, thumbnail_location, True)

        self.assertEquals(output["display_name"], "my_file")
        self.assertEquals(output["date_added"], "Jun 01, 2013 at 10:30 UTC")
        self.assertEquals(output["url"], "/i4x/foo/bar/asset/my_file_name.jpg")
        self.assertEquals(output["portable_url"], "/static/my_file_name.jpg")
        self.assertEquals(output["thumbnail"], "/i4x/foo/bar/asset/my_file_name_thumb.jpg")
        self.assertEquals(output["id"], output["url"])
        self.assertEquals(output['locked'], True)

        output = assets._get_asset_json("name", upload_date, location, None, False)
        self.assertIsNone(output["thumbnail"])


class LockAssetTestCase(CourseTestCase):
    """
    Unit test for locking and unlocking an asset.
    """

    def test_locking(self):
        """
        Tests a simple locking and unlocking of an asset in the toy course.
        """
        def verify_asset_locked_state(locked):
            """ Helper method to verify lock state in the contentstore """
            asset_location = StaticContent.get_location_from_path('/c4x/edX/toy/asset/sample_static.txt')
            content = contentstore().find(asset_location)
            self.assertEqual(content.locked, locked)

        def post_asset_update(lock):
            """ Helper method for posting asset update. """
            upload_date = datetime(2013, 6, 1, 10, 30, tzinfo=UTC)
            asset_location = Location(['c4x', 'edX', 'toy', 'asset', 'sample_static.txt'])
            location = loc_mapper().translate_location(course.location.course_id, course.location, False, True)
            url = location.url_reverse('assets/', '')

            resp = self.client.post(
                url,
                json.dumps(assets._get_asset_json("sample_static.txt", upload_date, asset_location, None, lock)),
                "application/json"
            )
            self.assertEqual(resp.status_code, 201)
            return json.loads(resp.content)

        # Load the toy course.
        module_store = modulestore('direct')
        _, course_items = import_from_xml(
            module_store,
            'common/test/data/',
            ['toy'],
            static_content_store=contentstore(),
            verbose=True
        )
        course = course_items[0]
        verify_asset_locked_state(False)

        # Lock the asset
        resp_asset = post_asset_update(True)
        self.assertTrue(resp_asset['locked'])
        verify_asset_locked_state(True)

        # Unlock the asset
        resp_asset = post_asset_update(False)
        self.assertFalse(resp_asset['locked'])
        verify_asset_locked_state(False)
