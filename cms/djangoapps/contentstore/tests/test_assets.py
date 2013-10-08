"""
Unit tests for the asset upload endpoint.
"""

#pylint: disable=C0111
#pylint: disable=W0621
#pylint: disable=W0212

from datetime import datetime
from io import BytesIO
from pytz import UTC
from unittest import TestCase, skip
from .utils import CourseTestCase
from django.core.urlresolvers import reverse
from contentstore.views import assets
from xmodule.contentstore.content import StaticContent
from xmodule.modulestore import Location
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_importer import import_from_xml
import json


class AssetsTestCase(CourseTestCase):
    def setUp(self):
        super(AssetsTestCase, self).setUp()
        self.url = reverse("asset_index", kwargs={
            'org': self.course.location.org,
            'course': self.course.location.course,
            'name': self.course.location.name,
        })

    def test_basic(self):
        resp = self.client.get(self.url)
        self.assertEquals(resp.status_code, 200)

    def test_static_url_generation(self):
        location = Location(['i4x', 'foo', 'bar', 'asset', 'my_file_name.jpg'])
        path = StaticContent.get_static_path_from_location(location)
        self.assertEquals(path, '/static/my_file_name.jpg')


class AssetsToyCourseTestCase(CourseTestCase):
    """
    Tests the assets returned from asset_index for the toy test course.
    """
    def test_toy_assets(self):
        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'], static_content_store=contentstore(), verbose=True)
        url = reverse("asset_index", kwargs={'org': 'edX', 'course': 'toy', 'name': '2012_Fall'})

        resp = self.client.get(url)
        # Test a small portion of the asset data passed to the client.
        self.assertContains(resp, "new AssetCollection([{")
        self.assertContains(resp, "/c4x/edX/toy/asset/handouts_sample_handout.txt")


class UploadTestCase(CourseTestCase):
    """
    Unit tests for uploading a file
    """
    def setUp(self):
        super(UploadTestCase, self).setUp()
        self.url = reverse("upload_asset", kwargs={
            'org': self.course.location.org,
            'course': self.course.location.course,
            'coursename': self.course.location.name,
        })

    @skip("CorruptGridFile error on continuous integration server")
    def test_happy_path(self):
        f = BytesIO("sample content")
        f.name = "sample.txt"
        resp = self.client.post(self.url, {"name": "my-name", "file": f})
        self.assertEquals(resp.status_code, 200)

    def test_no_file(self):
        resp = self.client.post(self.url, {"name": "file.txt"})
        self.assertEquals(resp.status_code, 400)

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEquals(resp.status_code, 405)


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
            location = Location(['c4x', 'edX', 'toy', 'asset', 'sample_static.txt'])
            url = reverse('update_asset', kwargs={'org': 'edX', 'course': 'toy', 'name': '2012_Fall'})

            resp = self.client.post(url, json.dumps(assets._get_asset_json("sample_static.txt", upload_date, location, None, lock)), "application/json")
            self.assertEqual(resp.status_code, 201)
            return json.loads(resp.content)

        # Load the toy course.
        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'], static_content_store=contentstore(), verbose=True)
        verify_asset_locked_state(False)

        # Lock the asset
        resp_asset = post_asset_update(True)
        self.assertTrue(resp_asset['locked'])
        verify_asset_locked_state(True)

        # Unlock the asset
        resp_asset = post_asset_update(False)
        self.assertFalse(resp_asset['locked'])
        verify_asset_locked_state(False)
