"""
 Test contentstore.mongo functionality
"""
import logging
from uuid import uuid4
import unittest
import mimetypes
from tempfile import mkdtemp
import path
import shutil

from opaque_keys.edx.locator import CourseLocator, AssetLocator
from opaque_keys.edx.keys import AssetKey
from xmodule.tests import DATA_DIR
from xmodule.contentstore.mongo import MongoContentStore
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError
import ddt
from __builtin__ import delattr
from xmodule.modulestore.tests.mongo_connection import MONGO_PORT_NUM, MONGO_HOST

log = logging.getLogger(__name__)

HOST = MONGO_HOST
PORT = MONGO_PORT_NUM
DB = 'test_mongo_%s' % uuid4().hex[:5]


@ddt.ddt
class TestContentstore(unittest.TestCase):
    """
    Test the methods in contentstore.mongo using deprecated and non-deprecated keys
    """

    # don't use these 2 class vars as they restore behavior once the tests are done
    asset_deprecated = None
    ssck_deprecated = None

    @classmethod
    def tearDownClass(cls):
        """
        Restores deprecated values
        """
        if cls.asset_deprecated is not None:
            setattr(AssetLocator, 'deprecated', cls.asset_deprecated)
        else:
            delattr(AssetLocator, 'deprecated')
        if cls.ssck_deprecated is not None:
            setattr(CourseLocator, 'deprecated', cls.ssck_deprecated)
        else:
            delattr(CourseLocator, 'deprecated')
        return super(TestContentstore, cls).tearDownClass()

    def set_up_assets(self, deprecated):
        """
        Setup contentstore w/ proper overriding of deprecated.
        """
        # since MongoModuleStore and MongoContentStore are basically assumed to be together, create this class
        # as well
        self.contentstore = MongoContentStore(HOST, DB, port=PORT)
        self.addCleanup(self.contentstore._drop_database)  # pylint: disable=protected-access

        setattr(AssetLocator, 'deprecated', deprecated)
        setattr(CourseLocator, 'deprecated', deprecated)

        self.course1_key = CourseLocator('test', 'asset_test', '2014_07')
        self.course2_key = CourseLocator('test', 'asset_test2', '2014_07')

        self.course1_files = ['contains.sh', 'picture1.jpg', 'picture2.jpg']
        self.course2_files = ['picture1.jpg', 'picture3.jpg', 'door_2.ogg']

        def load_assets(course_key, files):
            locked = False
            for filename in files:
                asset_key = course_key.make_asset_key('asset', filename)
                self.save_asset(filename, asset_key, filename, locked)
                locked = not locked

        load_assets(self.course1_key, self.course1_files)
        load_assets(self.course2_key, self.course2_files)

    def save_asset(self, filename, asset_key, displayname, locked):
        """
        Load and save the given file.
        """
        with open("{}/static/{}".format(DATA_DIR, filename), "rb") as f:
            content = StaticContent(
                asset_key, displayname, mimetypes.guess_type(filename)[0], f.read(),
                locked=locked
            )
            self.contentstore.save(content)

    @ddt.data(True, False)
    def test_delete(self, deprecated):
        """
        Test that deleting assets works
        """
        self.set_up_assets(deprecated)
        asset_key = self.course1_key.make_asset_key('asset', self.course1_files[0])
        self.contentstore.delete(asset_key)

        with self.assertRaises(NotFoundError):
            self.contentstore.find(asset_key)

        # ensure deleting a non-existent file is a noop
        self.contentstore.delete(asset_key)

    @ddt.data(True, False)
    def test_find(self, deprecated):
        """
        Test using find
        """
        self.set_up_assets(deprecated)
        asset_key = self.course1_key.make_asset_key('asset', self.course1_files[0])
        self.assertIsNotNone(self.contentstore.find(asset_key), "Could not find {}".format(asset_key))

        self.assertIsNotNone(self.contentstore.find(asset_key, as_stream=True), "Could not find {}".format(asset_key))

        unknown_asset = self.course1_key.make_asset_key('asset', 'no_such_file.gif')
        with self.assertRaises(NotFoundError):
            self.contentstore.find(unknown_asset)
        self.assertIsNone(
            self.contentstore.find(unknown_asset, throw_on_not_found=False),
            "Found unknown asset {}".format(unknown_asset)
        )

    @ddt.data(True, False)
    def test_export_for_course(self, deprecated):
        """
        Test export
        """
        self.set_up_assets(deprecated)
        root_dir = path.path(mkdtemp())
        try:
            self.contentstore.export_all_for_course(
                self.course1_key, root_dir,
                path.path(root_dir / "policy.json"),
            )
            for filename in self.course1_files:
                filepath = path.path(root_dir / filename)
                self.assertTrue(filepath.isfile(), "{} is not a file".format(filepath))
            for filename in self.course2_files:
                if filename not in self.course1_files:
                    filepath = path.path(root_dir / filename)
                    self.assertFalse(filepath.isfile(), "{} is unexpected exported a file".format(filepath))
        finally:
            shutil.rmtree(root_dir)

    @ddt.data(True, False)
    def test_get_all_content(self, deprecated):
        """
        Test get_all_content_for_course
        """
        self.set_up_assets(deprecated)
        course1_assets, count = self.contentstore.get_all_content_for_course(self.course1_key)
        self.assertEqual(count, len(self.course1_files), course1_assets)
        for asset in course1_assets:
            parsed = AssetKey.from_string(asset['filename'])
            self.assertIn(parsed.name, self.course1_files)

        course1_assets, __ = self.contentstore.get_all_content_for_course(self.course1_key, 1, 1)
        self.assertEqual(len(course1_assets), 1, course1_assets)

        fake_course = CourseLocator('test', 'fake', 'non')
        course_assets, count = self.contentstore.get_all_content_for_course(fake_course)
        self.assertEqual(count, 0)
        self.assertEqual(course_assets, [])

    @ddt.data(True, False)
    def test_attrs(self, deprecated):
        """
        Test setting and getting attrs
        """
        self.set_up_assets(deprecated)
        for filename in self.course1_files:
            asset_key = self.course1_key.make_asset_key('asset', filename)
            prelocked = self.contentstore.get_attr(asset_key, 'locked', False)
            self.contentstore.set_attr(asset_key, 'locked', not prelocked)
            self.assertEqual(self.contentstore.get_attr(asset_key, 'locked', False), not prelocked)

    @ddt.data(True, False)
    def test_copy_assets(self, deprecated):
        """
        copy_all_course_assets
        """
        self.set_up_assets(deprecated)
        dest_course = CourseLocator('test', 'destination', 'copy')
        self.contentstore.copy_all_course_assets(self.course1_key, dest_course)
        for filename in self.course1_files:
            asset_key = self.course1_key.make_asset_key('asset', filename)
            dest_key = dest_course.make_asset_key('asset', filename)
            source = self.contentstore.find(asset_key)
            copied = self.contentstore.find(dest_key)
            for propname in ['name', 'content_type', 'length', 'locked']:
                self.assertEqual(getattr(source, propname), getattr(copied, propname))

        __, count = self.contentstore.get_all_content_for_course(dest_course)
        self.assertEqual(count, len(self.course1_files))

    @ddt.data(True, False)
    def test_delete_assets(self, deprecated):
        """
        delete_all_course_assets
        """
        self.set_up_assets(deprecated)
        self.contentstore.delete_all_course_assets(self.course1_key)
        __, count = self.contentstore.get_all_content_for_course(self.course1_key)
        self.assertEqual(count, 0)
        # ensure it didn't remove any from other course
        __, count = self.contentstore.get_all_content_for_course(self.course2_key)
        self.assertEqual(count, len(self.course2_files))
