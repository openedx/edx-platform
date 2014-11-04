"""
Tests for assetstore using any of the modulestores for metadata. May extend to testing the storage options
too.
"""
from datetime import datetime, timedelta
import pytz
import unittest
import ddt

from xmodule.assetstore import AssetMetadata, AssetThumbnailMetadata
from xmodule.modulestore import ModuleStoreEnum

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.test_cross_modulestore_import_export import (
    MODULESTORE_SETUPS, MongoContentstoreBuilder, XmlModulestoreBuilder, MixedModulestoreBuilder, MongoModulestoreBuilder
)


@ddt.ddt
class TestMongoAssetMetadataStorage(unittest.TestCase):
    """
    Tests for storing/querying course asset metadata.
    """
    def setUp(self):
        super(TestMongoAssetMetadataStorage, self).setUp()
        self.addTypeEqualityFunc(datetime, self._compare_datetimes)
        self.addTypeEqualityFunc(AssetMetadata, self._compare_metadata)

    def _compare_metadata(self, mdata1, mdata2, msg=None):
        """
        So we can use the below date comparison
        """
        if type(mdata1) != type(mdata2):
            self.fail(self._formatMessage(msg, u"{} is not same type as {}".format(mdata1, mdata2)))
        for attr in mdata1.ALLOWED_ATTRS:
            self.assertEqual(getattr(mdata1, attr), getattr(mdata2, attr), msg)

    def _compare_datetimes(self, datetime1, datetime2, msg=None):
        """
        Don't compare microseconds as mongo doesn't encode below milliseconds
        """
        if not timedelta(seconds=-1) < datetime1 - datetime2 < timedelta(seconds=1):
            self.fail(self._formatMessage(msg, u"{} != {}".format(datetime1, datetime2)))

    def _make_asset_metadata(self, asset_loc):
        """
        Make a single test asset metadata.
        """
        return AssetMetadata(asset_loc, internal_name='EKMND332DDBK',
                             basename='pictures/historical', contenttype='image/jpeg',
                             locked=False, md5='77631ca4f0e08419b70726a447333ab6',
                             edited_by=ModuleStoreEnum.UserID.test, edited_on=datetime.now(pytz.utc),
                             curr_version='v1.0', prev_version='v0.95')

    def _make_asset_thumbnail_metadata(self, asset_key):
        """
        Make a single test asset thumbnail metadata.
        """
        return AssetThumbnailMetadata(asset_key, internal_name='ABC39XJUDN2')

    def setup_assets(self, course1_key, course2_key, store=None):
        """
        Setup assets. Save in store if given
        """
        asset_fields = ('filename', 'internal_name', 'basename', 'locked', 'edited_by', 'edited_on', 'curr_version', 'prev_version')
        all_asset_data = (
            ('pic1.jpg', 'EKMND332DDBK', 'pix/archive', False, ModuleStoreEnum.UserID.test, datetime.now(pytz.utc), '14', '13'),
            ('shout.ogg', 'KFMDONSKF39K', 'sounds', True, ModuleStoreEnum.UserID.test, datetime.now(pytz.utc), '1', None),
            ('code.tgz', 'ZZB2333YBDMW', 'exercises/14', False, ModuleStoreEnum.UserID.test * 2, datetime.now(pytz.utc), 'AB', 'AA'),
            ('dog.png', 'PUPY4242X', 'pictures/animals', True, ModuleStoreEnum.UserID.test * 3, datetime.now(pytz.utc), '5', '4'),
            ('not_here.txt', 'JJJCCC747', '/dev/null', False, ModuleStoreEnum.UserID.test * 4, datetime.now(pytz.utc), '50', '49'),
            ('asset.txt', 'JJJCCC747858', '/dev/null', False, ModuleStoreEnum.UserID.test * 4, datetime.now(pytz.utc), '50', '49'),
            ('roman_history.pdf', 'JASDUNSADK', 'texts/italy', True, ModuleStoreEnum.UserID.test * 7, datetime.now(pytz.utc), '1.1', '1.01'),
            ('weather_patterns.bmp', '928SJXX2EB', 'science', False, ModuleStoreEnum.UserID.test * 8, datetime.now(pytz.utc), '52', '51'),
            ('demo.swf', 'DFDFGGGG14', 'demos/easy', False, ModuleStoreEnum.UserID.test * 9, datetime.now(pytz.utc), '5', '4'),
        )

        for i, asset in enumerate(all_asset_data):
            asset_dict = dict(zip(asset_fields[1:], asset[1:]))
            if i in (0, 1) and course1_key:
                asset_key = course1_key.make_asset_key('asset', asset[0])
                asset_md = AssetMetadata(asset_key, **asset_dict)
                if store is not None:
                    store.save_asset_metadata(course1_key, asset_md, asset[4])
            elif course2_key:
                asset_key = course2_key.make_asset_key('asset', asset[0])
                asset_md = AssetMetadata(asset_key, **asset_dict)
                # Don't save assets 5 and 6.
                if store is not None and i not in (4, 5):
                    store.save_asset_metadata(course2_key, asset_md, asset[4])

    def setup_thumbnails(self, course1_key, course2_key, store=None):
        """
        Setup thumbs. Save in store if given
        """
        thumbnail_fields = ('filename', 'internal_name')
        all_thumbnail_data = (
            ('cat_thumb.jpg', 'XYXYXYXYXYXY'),
            ('kitten_thumb.jpg', '123ABC123ABC'),
            ('puppy_thumb.jpg', 'ADAM12ADAM12'),
            ('meerkat_thumb.jpg', 'CHIPSPONCH14'),
            ('corgi_thumb.jpg', 'RON8LDXFFFF10'),
        )

        for i, thumb in enumerate(all_thumbnail_data):
            thumb_dict = dict(zip(thumbnail_fields[1:], thumb[1:]))
            if i in (0, 1) and course1_key:
                thumb_key = course1_key.make_asset_key('thumbnail', thumb[0])
                thumb_md = AssetThumbnailMetadata(thumb_key, **thumb_dict)
                if store is not None:
                    store.save_asset_thumbnail_metadata(course1_key, thumb_md, ModuleStoreEnum.UserID.test)
            elif course2_key:
                thumb_key = course2_key.make_asset_key('thumbnail', thumb[0])
                thumb_md = AssetThumbnailMetadata(thumb_key, **thumb_dict)
                # Don't save assets 5 and 6.
                if store is not None and i not in (4, 5):
                    store.save_asset_thumbnail_metadata(course2_key, thumb_md, ModuleStoreEnum.UserID.test)


    @ddt.data(*MODULESTORE_SETUPS)
    def test_save_one_and_confirm(self, storebuilder):
        """
        Save the metadata in each store and retrieve it singularly, as all assets, and after deleting all.
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course = CourseFactory.create(modulestore=store)

                asset_filename = 'burnside.jpg'
                new_asset_loc = course.id.make_asset_key('asset', asset_filename)
                # Confirm that the asset's metadata is not present.
                self.assertIsNone(store.find_asset_metadata(new_asset_loc))
                # Save the asset's metadata.
                new_asset_md = self._make_asset_metadata(new_asset_loc)
                store.save_asset_metadata(course.id, new_asset_md, ModuleStoreEnum.UserID.test)
                # Find the asset's metadata and confirm it's the same.
                found_asset_md = store.find_asset_metadata(new_asset_loc)
                self.assertIsNotNone(found_asset_md)
                self.assertEquals(new_asset_md, found_asset_md)
                # Confirm that only two setup plus one asset's metadata exists.
                self.assertEquals(len(store.get_all_asset_metadata(course.id)), 1)
                # Delete all metadata and confirm it's gone.
                store.delete_all_asset_metadata(course.id, ModuleStoreEnum.UserID.test)
                self.assertEquals(len(store.get_all_asset_metadata(course.id)), 0)
                # Now delete the non-existent metadata and ensure it doesn't choke
                store.delete_all_asset_metadata(course.id, ModuleStoreEnum.UserID.test)
                self.assertEquals(len(store.get_all_asset_metadata(course.id)), 0)

    @ddt.data(*MODULESTORE_SETUPS)
    def test_delete(self, storebuilder):
        """
        Delete non_existent and existent metadata
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course = CourseFactory.create(modulestore=store)
                new_asset_loc = course.id.make_asset_key('asset', 'burnside.jpg')
                # Attempt to delete an asset that doesn't exist.
                self.assertEquals(store.delete_asset_metadata(new_asset_loc, ModuleStoreEnum.UserID.test), 0)
                self.assertEquals(len(store.get_all_asset_metadata(course.id)), 0)

                new_asset_md = self._make_asset_metadata(new_asset_loc)
                store.save_asset_metadata(course.id, new_asset_md, ModuleStoreEnum.UserID.test)
                self.assertEquals(store.delete_asset_metadata(new_asset_loc, ModuleStoreEnum.UserID.test), 1)
                self.assertEquals(len(store.get_all_asset_metadata(course.id)), 0)

    @ddt.data(*MODULESTORE_SETUPS)
    def test_find_non_existing_assets(self, storebuilder):
        """
        Save multiple metadata in each store and retrieve it singularly, as all assets, and after deleting all.
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course = CourseFactory.create(modulestore=store)
                new_asset_loc = course.id.make_asset_key('asset', 'burnside.jpg')
                # Find existing asset metadata.
                asset_md = store.find_asset_metadata(new_asset_loc)
                self.assertIsNone(asset_md)

    @ddt.data(*MODULESTORE_SETUPS)
    def test_add_same_asset_twice(self, storebuilder):
        """
        Save multiple metadata in each store and retrieve it singularly, as all assets, and after deleting all.
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course = CourseFactory.create(modulestore=store)
                new_asset_loc = course.id.make_asset_key('asset', 'burnside.jpg')
                new_asset_md = self._make_asset_metadata(new_asset_loc)
                # Add asset metadata.
                store.save_asset_metadata(course.id, new_asset_md, ModuleStoreEnum.UserID.test)
                self.assertEquals(len(store.get_all_asset_metadata(course.id)), 1)
                # Add *the same* asset metadata.
                store.save_asset_metadata(course.id, new_asset_md, ModuleStoreEnum.UserID.test)
                # Still one here?
                self.assertEquals(len(store.get_all_asset_metadata(course.id)), 1)
                store.delete_all_asset_metadata(course.id, ModuleStoreEnum.UserID.test)
                self.assertEquals(len(store.get_all_asset_metadata(course.id)), 0)

    @ddt.data(*MODULESTORE_SETUPS)
    def test_lock_unlock_assets(self, storebuilder):
        """
        Save multiple metadata in each store and retrieve it singularly, as all assets, and after deleting all.
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course = CourseFactory.create(modulestore=store)
                new_asset_loc = course.id.make_asset_key('asset', 'burnside.jpg')
                new_asset_md = self._make_asset_metadata(new_asset_loc)
                store.save_asset_metadata(course.id, new_asset_md, ModuleStoreEnum.UserID.test)

                locked_state = new_asset_md.locked
                # Flip the course asset's locked status.
                store.set_asset_metadata_attr(new_asset_loc, "locked", not locked_state, ModuleStoreEnum.UserID.test)
                # Find the same course and check its locked status.
                updated_asset_md = store.find_asset_metadata(new_asset_loc)
                self.assertIsNotNone(updated_asset_md)
                self.assertEquals(updated_asset_md.locked, not locked_state)
                # Now flip it back.
                store.set_asset_metadata_attr(new_asset_loc, "locked", locked_state, ModuleStoreEnum.UserID.test)
                reupdated_asset_md = store.find_asset_metadata(new_asset_loc)
                self.assertIsNotNone(reupdated_asset_md)
                self.assertEquals(reupdated_asset_md.locked, locked_state)

    ALLOWED_ATTRS = (
        ('basename', '/new/path'),
        ('internal_name', 'new_filename.txt'),
        ('locked', True),
        ('contenttype', 'image/png'),
        ('md5', '5346682d948cc3f683635b6918f9b3d0'),
        ('curr_version', 'v1.01'),
        ('prev_version', 'v1.0'),
        ('edited_by', 'Mork'),
        ('edited_on', datetime(1969, 1, 1, tzinfo=pytz.utc)),
    )

    DISALLOWED_ATTRS = (
        ('asset_id', 'IAmBogus'),
    )

    UNKNOWN_ATTRS = (
        ('lunch_order', 'burger_and_fries'),
        ('villain', 'Khan')
    )

    @ddt.data(*MODULESTORE_SETUPS)
    def test_set_all_attrs(self, storebuilder):
        """
        Save setting each attr one at a time
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course = CourseFactory.create(modulestore=store)
                new_asset_loc = course.id.make_asset_key('asset', 'burnside.jpg')
                new_asset_md = self._make_asset_metadata(new_asset_loc)
                store.save_asset_metadata(course.id, new_asset_md, ModuleStoreEnum.UserID.test)
                for attr, value in self.ALLOWED_ATTRS:
                    # Set the course asset's attr.
                    store.set_asset_metadata_attr(new_asset_loc, attr, value, ModuleStoreEnum.UserID.test)
                    # Find the same course asset and check its changed attr.
                    updated_asset_md = store.find_asset_metadata(new_asset_loc)
                    self.assertIsNotNone(updated_asset_md)
                    self.assertIsNotNone(getattr(updated_asset_md, attr, None))
                    self.assertEquals(getattr(updated_asset_md, attr, None), value)

    @ddt.data(*MODULESTORE_SETUPS)
    def test_set_disallowed_attrs(self, storebuilder):
        """
        setting disallowed attrs should fail
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course = CourseFactory.create(modulestore=store)
                new_asset_loc = course.id.make_asset_key('asset', 'burnside.jpg')
                new_asset_md = self._make_asset_metadata(new_asset_loc)
                store.save_asset_metadata(course.id, new_asset_md, ModuleStoreEnum.UserID.test)
                for attr, value in self.DISALLOWED_ATTRS:
                    original_attr_val = getattr(new_asset_md, attr)
                    # Set the course asset's attr.
                    store.set_asset_metadata_attr(new_asset_loc, attr, value, ModuleStoreEnum.UserID.test)
                    # Find the same course and check its changed attr.
                    updated_asset_md = store.find_asset_metadata(new_asset_loc)
                    self.assertIsNotNone(updated_asset_md)
                    self.assertIsNotNone(getattr(updated_asset_md, attr, None))
                    # Make sure that the attr is unchanged from its original value.
                    self.assertEquals(getattr(updated_asset_md, attr, None), original_attr_val)

    @ddt.data(*MODULESTORE_SETUPS)
    def test_set_unknown_attrs(self, storebuilder):
        """
        setting unknown attrs should fail
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course = CourseFactory.create(modulestore=store)
                new_asset_loc = course.id.make_asset_key('asset', 'burnside.jpg')
                new_asset_md = self._make_asset_metadata(new_asset_loc)
                store.save_asset_metadata(course.id, new_asset_md, ModuleStoreEnum.UserID.test)
                for attr, value in self.UNKNOWN_ATTRS:
                    # Set the course asset's attr.
                    store.set_asset_metadata_attr(new_asset_loc, attr, value, ModuleStoreEnum.UserID.test)
                    # Find the same course and check its changed attr.
                    updated_asset_md = store.find_asset_metadata(new_asset_loc)
                    self.assertIsNotNone(updated_asset_md)
                    # Make sure the unknown field was *not* added.
                    with self.assertRaises(AttributeError):
                        self.assertEquals(getattr(updated_asset_md, attr), value)

    @ddt.data(*MODULESTORE_SETUPS)
    def test_save_one_thumbnail_and_delete_one_thumbnail(self, storebuilder):
        """
        saving and deleting thumbnails
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course = CourseFactory.create(modulestore=store)
                thumbnail_filename = 'burn_thumb.jpg'
                asset_key = course.id.make_asset_key('thumbnail', thumbnail_filename)
                new_asset_thumbnail = self._make_asset_thumbnail_metadata(asset_key)
                store.save_asset_thumbnail_metadata(course.id, new_asset_thumbnail, ModuleStoreEnum.UserID.test)
                self.assertEquals(len(store.get_all_asset_thumbnail_metadata(course.id)), 1)
                self.assertEquals(store.delete_asset_thumbnail_metadata(asset_key, ModuleStoreEnum.UserID.test), 1)
                self.assertEquals(len(store.get_all_asset_thumbnail_metadata(course.id)), 0)

    @ddt.data(*MODULESTORE_SETUPS)
    def test_find_thumbnail(self, storebuilder):
        """
        finding thumbnails
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course = CourseFactory.create(modulestore=store)
                thumbnail_filename = 'burn_thumb.jpg'
                asset_key = course.id.make_asset_key('thumbnail', thumbnail_filename)
                new_asset_thumbnail = self._make_asset_thumbnail_metadata(asset_key)
                store.save_asset_thumbnail_metadata(course.id, new_asset_thumbnail, ModuleStoreEnum.UserID.test)

                self.assertIsNotNone(store.find_asset_thumbnail_metadata(asset_key))
                unknown_asset_key = course.id.make_asset_key('thumbnail', 'nosuchfile.jpg')
                self.assertIsNone(store.find_asset_thumbnail_metadata(unknown_asset_key))

    @ddt.data(*MODULESTORE_SETUPS)
    def test_delete_all_thumbnails(self, storebuilder):
        """
        deleting all thumbnails
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course = CourseFactory.create(modulestore=store)
                thumbnail_filename = 'burn_thumb.jpg'
                asset_key = course.id.make_asset_key('thumbnail', thumbnail_filename)
                new_asset_thumbnail = self._make_asset_thumbnail_metadata(asset_key)
                store.save_asset_thumbnail_metadata(
                    course.id, new_asset_thumbnail, ModuleStoreEnum.UserID.test
                )

                self.assertEquals(len(store.get_all_asset_thumbnail_metadata(course.id)), 1)
                store.delete_all_asset_metadata(course.id, ModuleStoreEnum.UserID.test)
                self.assertEquals(len(store.get_all_asset_thumbnail_metadata(course.id)), 0)

    @ddt.data(*MODULESTORE_SETUPS)
    def test_get_all_assets_with_paging(self, storebuilder):
        """
        Save multiple metadata in each store and retrieve it singularly, as all assets, and after deleting all.
        """
        # Temporarily only perform this test for Old Mongo - not Split.
        if not isinstance(storebuilder, MongoModulestoreBuilder):
            raise unittest.SkipTest
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course1 = CourseFactory.create(modulestore=store)
                course2 = CourseFactory.create(modulestore=store)
                self.setup_assets(course1.id, course2.id, store)

                expected_sorts_by_2 = (
                    (
                        ('displayname', ModuleStoreEnum.SortOrder.ascending),
                        ('code.tgz', 'demo.swf', 'dog.png', 'roman_history.pdf', 'weather_patterns.bmp'),
                        (2, 2, 1)
                    ),
                    (
                        ('displayname', ModuleStoreEnum.SortOrder.descending),
                        ('weather_patterns.bmp', 'roman_history.pdf', 'dog.png', 'demo.swf', 'code.tgz'),
                        (2, 2, 1)
                    ),
                    (
                        ('uploadDate', ModuleStoreEnum.SortOrder.ascending),
                        ('code.tgz', 'dog.png', 'roman_history.pdf', 'weather_patterns.bmp', 'demo.swf'),
                        (2, 2, 1)
                    ),
                    (
                        ('uploadDate', ModuleStoreEnum.SortOrder.descending),
                        ('demo.swf', 'weather_patterns.bmp', 'roman_history.pdf', 'dog.png', 'code.tgz'),
                        (2, 2, 1)
                    ),
                )
                # First, with paging across all sorts.
                for sort_test in expected_sorts_by_2:
                    for i in xrange(3):
                        asset_page = store.get_all_asset_metadata(course2.id, start=2 * i, maxresults=2, sort=sort_test[0])
                        self.assertEquals(len(asset_page), sort_test[2][i])
                        self.assertEquals(asset_page[0].asset_id.path, sort_test[1][2 * i])
                        if sort_test[2][i] == 2:
                            self.assertEquals(asset_page[1].asset_id.path, sort_test[1][(2 * i) + 1])

                # Now fetch everything.
                asset_page = store.get_all_asset_metadata(course2.id, start=0, sort=('displayname', ModuleStoreEnum.SortOrder.ascending))
                self.assertEquals(len(asset_page), 5)
                self.assertEquals(asset_page[0].asset_id.path, 'code.tgz')
                self.assertEquals(asset_page[1].asset_id.path, 'demo.swf')
                self.assertEquals(asset_page[2].asset_id.path, 'dog.png')
                self.assertEquals(asset_page[3].asset_id.path, 'roman_history.pdf')
                self.assertEquals(asset_page[4].asset_id.path, 'weather_patterns.bmp')

                # Some odd conditions.
                asset_page = store.get_all_asset_metadata(course2.id, start=100, sort=('uploadDate', ModuleStoreEnum.SortOrder.ascending))
                self.assertEquals(len(asset_page), 0)
                asset_page = store.get_all_asset_metadata(course2.id, start=3, maxresults=0, sort=('displayname', ModuleStoreEnum.SortOrder.ascending))
                self.assertEquals(len(asset_page), 0)
                asset_page = store.get_all_asset_metadata(course2.id, start=3, maxresults=-12345, sort=('displayname', ModuleStoreEnum.SortOrder.descending))
                self.assertEquals(len(asset_page), 2)

    @ddt.data(XmlModulestoreBuilder(), MixedModulestoreBuilder([('xml', XmlModulestoreBuilder())]))
    def test_xml_not_yet_implemented(self, storebuilder):
        """
        Test coverage which shows that for now xml read operations are not implemented
        """
        with storebuilder.build(None) as store:
            course_key = store.make_course_key("org", "course", "run")
            asset_key = course_key.make_asset_key('asset', 'foo.jpg')
            for method in ['_find_asset_info', 'find_asset_metadata', 'find_asset_thumbnail_metadata']:
                with self.assertRaises(NotImplementedError):
                    getattr(store, method)(asset_key)
            with self.assertRaises(NotImplementedError):
                # pylint: disable=protected-access
                store._find_course_asset(course_key, asset_key.block_id)
            for method in ['_get_all_asset_metadata', 'get_all_asset_metadata', 'get_all_asset_thumbnail_metadata']:
                with self.assertRaises(NotImplementedError):
                    getattr(store, method)(course_key)

    @ddt.data(*MODULESTORE_SETUPS)
    def test_copy_all_assets(self, storebuilder):
        """
        Create a course with assets and such, copy it all to another course, and check on it.
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with storebuilder.build(contentstore) as store:
                course1 = CourseFactory.create(modulestore=store)
                course2 = CourseFactory.create(modulestore=store)
                self.setup_assets(course1.id, None, store)
                self.setup_thumbnails(course1.id, None, store)
                self.assertEquals(len(store.get_all_asset_metadata(course1.id)), 2)
                self.assertEquals(len(store.get_all_asset_thumbnail_metadata(course1.id)), 2)
                self.assertEquals(len(store.get_all_asset_metadata(course2.id)), 0)
                self.assertEquals(len(store.get_all_asset_thumbnail_metadata(course2.id)), 0)
                store.copy_all_asset_metadata(course1.id, course2.id, ModuleStoreEnum.UserID.test * 101)
                self.assertEquals(len(store.get_all_asset_metadata(course1.id)), 2)
                self.assertEquals(len(store.get_all_asset_thumbnail_metadata(course1.id)), 2)
                all_assets = store.get_all_asset_metadata(course2.id, sort=('displayname', ModuleStoreEnum.SortOrder.ascending))
                self.assertEquals(len(all_assets), 2)
                self.assertEquals(all_assets[0].asset_id.path, 'pic1.jpg')
                self.assertEquals(all_assets[1].asset_id.path, 'shout.ogg')
                all_thumbnails = store.get_all_asset_thumbnail_metadata(course2.id, sort=('uploadDate', ModuleStoreEnum.SortOrder.descending))
                self.assertEquals(len(all_thumbnails), 2)
                self.assertEquals(all_thumbnails[0].asset_id.path, 'kitten_thumb.jpg')
                self.assertEquals(all_thumbnails[1].asset_id.path, 'cat_thumb.jpg')
