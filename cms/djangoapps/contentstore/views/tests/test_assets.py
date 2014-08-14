"""
Unit tests for the asset upload endpoint.
"""

# pylint: disable=C0111
# pylint: disable=W0621
# pylint: disable=W0212

from datetime import datetime
from io import BytesIO
from pytz import UTC
import json
from contentstore.tests.utils import CourseTestCase
from contentstore.views import assets
from contentstore.utils import reverse_course_url
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_importer import import_from_xml
from django.test.utils import override_settings
from opaque_keys.edx.locations import SlashSeparatedCourseKey, AssetLocation


class AssetsTestCase(CourseTestCase):
    """
    Parent class for all asset tests.
    """
    def setUp(self):
        super(AssetsTestCase, self).setUp()
        self.url = reverse_course_url('assets_handler', self.course.id)

    def upload_asset(self, name="asset-1"):
        f = BytesIO(name)
        f.name = name + ".txt"
        return self.client.post(self.url, {"name": name, "file": f})


class BasicAssetsTestCase(AssetsTestCase):
    def test_basic(self):
        resp = self.client.get(self.url, HTTP_ACCEPT='text/html')
        self.assertEquals(resp.status_code, 200)

    def test_static_url_generation(self):

        course_key = SlashSeparatedCourseKey('org', 'class', 'run')
        location = course_key.make_asset_key('asset', 'my_file_name.jpg')
        path = StaticContent.get_static_path_from_location(location)
        self.assertEquals(path, '/static/my_file_name.jpg')

    def test_pdf_asset(self):
        module_store = modulestore()
        course_items = import_from_xml(
            module_store,
            self.user.id,
            'common/test/data/',
            ['toy'],
            static_content_store=contentstore(),
            verbose=True
        )
        course = course_items[0]
        url = reverse_course_url('assets_handler', course.id)

        # Test valid contentType for pdf asset (textbook.pdf)
        resp = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertContains(resp, "/c4x/edX/toy/asset/textbook.pdf")
        asset_location = AssetLocation.from_deprecated_string('/c4x/edX/toy/asset/textbook.pdf')
        content = contentstore().find(asset_location)
        # Check after import textbook.pdf has valid contentType ('application/pdf')

        # Note: Actual contentType for textbook.pdf in asset.json is 'text/pdf'
        self.assertEqual(content.content_type, 'application/pdf')


class PaginationTestCase(AssetsTestCase):
    """
    Tests the pagination of assets returned from the REST API.
    """
    def test_json_responses(self):
        self.upload_asset("asset-1")
        self.upload_asset("asset-2")
        self.upload_asset("asset-3")

        # Verify valid page requests
        self.assert_correct_asset_response(self.url, 0, 3, 3)
        self.assert_correct_asset_response(self.url + "?page_size=2", 0, 2, 3)
        self.assert_correct_asset_response(self.url + "?page_size=2&page=1", 2, 1, 3)
        self.assert_correct_sort_response(self.url, 'date_added', 'asc')
        self.assert_correct_sort_response(self.url, 'date_added', 'desc')
        self.assert_correct_sort_response(self.url, 'display_name', 'asc')
        self.assert_correct_sort_response(self.url, 'display_name', 'desc')

        # Verify querying outside the range of valid pages
        self.assert_correct_asset_response(self.url + "?page_size=2&page=-1", 0, 2, 3)
        self.assert_correct_asset_response(self.url + "?page_size=2&page=2", 2, 1, 3)
        self.assert_correct_asset_response(self.url + "?page_size=3&page=1", 0, 3, 3)

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


class UploadTestCase(AssetsTestCase):
    """
    Unit tests for uploading a file
    """
    def setUp(self):
        super(UploadTestCase, self).setUp()
        self.url = reverse_course_url('assets_handler', self.course.id)

    def test_happy_path(self):
        resp = self.upload_asset()
        self.assertEquals(resp.status_code, 200)

    def test_no_file(self):
        resp = self.client.post(self.url, {"name": "file.txt"}, "application/json")
        self.assertEquals(resp.status_code, 400)


class AssetToJsonTestCase(AssetsTestCase):
    """
    Unit test for transforming asset information into something
    we can send out to the client via JSON.
    """
    @override_settings(LMS_BASE="lms_base_url")
    def test_basic(self):
        upload_date = datetime(2013, 6, 1, 10, 30, tzinfo=UTC)

        course_key = SlashSeparatedCourseKey('org', 'class', 'run')
        location = course_key.make_asset_key('asset', 'my_file_name.jpg')
        thumbnail_location = course_key.make_asset_key('thumbnail', 'my_file_name_thumb.jpg')

        output = assets._get_asset_json("my_file", upload_date, location, thumbnail_location, True)

        self.assertEquals(output["display_name"], "my_file")
        self.assertEquals(output["date_added"], "Jun 01, 2013 at 10:30 UTC")
        self.assertEquals(output["url"], "/c4x/org/class/asset/my_file_name.jpg")
        self.assertEquals(output["external_url"], "lms_base_url/c4x/org/class/asset/my_file_name.jpg")
        self.assertEquals(output["portable_url"], "/static/my_file_name.jpg")
        self.assertEquals(output["thumbnail"], "/c4x/org/class/thumbnail/my_file_name_thumb.jpg")
        self.assertEquals(output["id"], unicode(location))
        self.assertEquals(output['locked'], True)

        output = assets._get_asset_json("name", upload_date, location, None, False)
        self.assertIsNone(output["thumbnail"])


class LockAssetTestCase(AssetsTestCase):
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

        def post_asset_update(lock, course):
            """ Helper method for posting asset update. """
            upload_date = datetime(2013, 6, 1, 10, 30, tzinfo=UTC)
            asset_location = course.id.make_asset_key('asset', 'sample_static.txt')
            url = reverse_course_url('assets_handler', course.id, kwargs={'asset_key_string': unicode(asset_location)})

            resp = self.client.post(
                url,
                json.dumps(assets._get_asset_json("sample_static.txt", upload_date, asset_location, None, lock)),
                "application/json"
            )
            self.assertEqual(resp.status_code, 201)
            return json.loads(resp.content)

        # Load the toy course.
        module_store = modulestore()
        course_items = import_from_xml(
            module_store,
            self.user.id,
            'common/test/data/',
            ['toy'],
            static_content_store=contentstore(),
            verbose=True
        )
        course = course_items[0]
        verify_asset_locked_state(False)

        # Lock the asset
        resp_asset = post_asset_update(True, course)
        self.assertTrue(resp_asset['locked'])
        verify_asset_locked_state(True)

        # Unlock the asset
        resp_asset = post_asset_update(False, course)
        self.assertFalse(resp_asset['locked'])
        verify_asset_locked_state(False)
