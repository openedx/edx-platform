"""
Unit tests for the asset upload endpoint.
"""

import os
import json
import shutil
import tarfile
import tempfile
from subprocess import call
from datetime import datetime
from io import BytesIO
from pytz import UTC
from unittest import TestCase, skip
from .utils import CourseTestCase
from django.core.urlresolvers import reverse
from contentstore.views import assets
from xmodule.contentstore.content import StaticContent
from xmodule.modulestore import Location


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

    def test_json(self):
        resp = self.client.get(
            self.url,
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEquals(resp.status_code, 200)
        content = json.loads(resp.content)
        self.assertIsInstance(content, list)

    def test_static_url_generation(self):
        location = Location(['i4x', 'foo', 'bar', 'asset', 'my_file_name.jpg'])
        path = StaticContent.get_static_path_from_location(location)
        self.assertEquals(path, '/static/my_file_name.jpg')


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
        self.assert2XX(resp.status_code)

    def test_no_file(self):
        resp = self.client.post(self.url, {"name": "file.txt"})
        self.assert4XX(resp.status_code)

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEquals(resp.status_code, 405)

class ImportTestCase(CourseTestCase):
    """
    Unit tests for importing a course
    """

    def setUp(self):
        super(ImportTestCase, self).setUp()
        self.url = reverse("import_course", kwargs={
            'org': self.course.location.org,
            'course': self.course.location.course,
            'name': self.course.location.name,
        })
        self.content_dir = tempfile.mkdtemp()

        def touch(name):
            """ Equivalent to shell's 'touch'"""
            with file(name, 'a'):
                os.utime(name, None)

        # Create tar test files
        good_dir = tempfile.mkdtemp(dir=self.content_dir)
        os.makedirs(os.path.join(good_dir, "course"))
        with open(os.path.join(good_dir, "course.xml") , "w+") as f:
            f.write('<course url_name="2013_Spring" org="EDx" course="0.00x"/>')

        with open(os.path.join(good_dir, "course", "2013_Spring.xml"), "w+") as f:
            f.write('<course></course>')


        self.good_tar = os.path.join(self.content_dir, "good.tar.gz")
        with tarfile.open(self.good_tar, "w:gz") as gtar:
            gtar.add(good_dir)

        bad_dir = tempfile.mkdtemp(dir=self.content_dir)
        touch(os.path.join(bad_dir, "bad.xml"))
        self.bad_tar = os.path.join(self.content_dir, "bad.tar.gz")
        with tarfile.open(self.bad_tar, "w:gz") as btar:
            btar.add(bad_dir)

    def tearDown(self):
        shutil.rmtree(self.content_dir)

    def test_no_coursexml(self):
        """
        Check that the response for a tar.gz import without a course.xml is
        correct.
        """
        with open(self.bad_tar) as btar:
            resp = self.client.post(
                    self.url,
                    {
                        "name": self.bad_tar,
                        "course-data": [btar]
                    })
        self.assertEquals(resp.status_code, 415)

    def test_with_coursexml(self):
        """
        Check that the response for a tar.gz import with a course.xml is
        correct.
        """
        with open(self.good_tar) as gtar:
            resp = self.client.post(
                    self.url,
                    {
                        "name": self.good_tar,
                        "course-data": [gtar]
                    })
        self.assert2XX(resp.status_code)




class AssetsToJsonTestCase(TestCase):
    """
    Unit tests for transforming the results of a database call into something
    we can send out to the client via JSON.
    """
    def test_basic(self):
        upload_date = datetime(2013, 6, 1, 10, 30, tzinfo=UTC)
        asset = {
            "displayname": "foo",
            "chunkSize": 512,
            "filename": "foo.png",
            "length": 100,
            "uploadDate": upload_date,
            "_id": {
                "course": "course",
                "org": "org",
                "revision": 12,
                "category": "category",
                "name": "name",
                "tag": "tag",
            }
        }
        output = assets.assets_to_json_dict([asset])
        self.assertEquals(len(output), 1)
        compare = output[0]
        self.assertEquals(compare["name"], "foo")
        self.assertEquals(compare["path"], "foo.png")
        self.assertEquals(compare["uploaded"], upload_date.isoformat())
        self.assertEquals(compare["id"], "/tag/org/course/12/category/name")
