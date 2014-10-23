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
    MODULESTORE_SETUPS, MongoContentstoreBuilder,
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
        asset1_vals = ('pic1.jpg', 'EKMND332DDBK', 'pix/archive', False, ModuleStoreEnum.UserID.test, datetime.now(pytz.utc), '14', '13')
        asset2_vals = ('shout.ogg', 'KFMDONSKF39K', 'sounds', True, ModuleStoreEnum.UserID.test, datetime.now(pytz.utc), '1', None)
        asset3_vals = ('code.tgz', 'ZZB2333YBDMW', 'exercises/14', False, ModuleStoreEnum.UserID.test * 2, datetime.now(pytz.utc), 'AB', 'AA')
        asset4_vals = ('dog.png', 'PUPY4242X', 'pictures/animals', True, ModuleStoreEnum.UserID.test * 3, datetime.now(pytz.utc), '5', '4')
        asset5_vals = ('not_here.txt', 'JJJCCC747', '/dev/null', False, ModuleStoreEnum.UserID.test * 4, datetime.now(pytz.utc), '50', '49')

        asset1 = dict(zip(asset_fields[1:], asset1_vals[1:]))
        asset2 = dict(zip(asset_fields[1:], asset2_vals[1:]))
        asset3 = dict(zip(asset_fields[1:], asset3_vals[1:]))
        asset4 = dict(zip(asset_fields[1:], asset4_vals[1:]))
        non_existent_asset = dict(zip(asset_fields[1:], asset5_vals[1:]))

        # Asset6 and thumbnail6 have equivalent information on purpose.
        asset6_vals = ('asset.txt', 'JJJCCC747858', '/dev/null', False, ModuleStoreEnum.UserID.test * 4, datetime.now(pytz.utc), '50', '49')
        asset6 = dict(zip(asset_fields[1:], asset6_vals[1:]))

        asset1_key = course1_key.make_asset_key('asset', asset1_vals[0])
        asset2_key = course1_key.make_asset_key('asset', asset2_vals[0])
        asset3_key = course2_key.make_asset_key('asset', asset3_vals[0])
        asset4_key = course2_key.make_asset_key('asset', asset4_vals[0])
        asset5_key = course2_key.make_asset_key('asset', asset5_vals[0])
        asset6_key = course2_key.make_asset_key('asset', asset6_vals[0])

        asset1_md = AssetMetadata(asset1_key, **asset1)
        asset2_md = AssetMetadata(asset2_key, **asset2)
        asset3_md = AssetMetadata(asset3_key, **asset3)
        asset4_md = AssetMetadata(asset4_key, **asset4)
        asset5_md = AssetMetadata(asset5_key, **non_existent_asset)
        asset6_md = AssetMetadata(asset6_key, **asset6)

        if store is not None:
            store.save_asset_metadata(course1_key, asset1_md, ModuleStoreEnum.UserID.test)
            store.save_asset_metadata(course1_key, asset2_md, ModuleStoreEnum.UserID.test)
            store.save_asset_metadata(course2_key, asset3_md, ModuleStoreEnum.UserID.test)
            store.save_asset_metadata(course2_key, asset4_md, ModuleStoreEnum.UserID.test)
            # 5 & 6 are not saved on purpose!

        return (asset1_md, asset2_md, asset3_md, asset4_md, asset5_md, asset6_md)

    def setup_thumbnails(self, course1_key, course2_key, store=None):
        """
        Setup thumbs. Save in store if given
        """
        thumbnail_fields = ('filename', 'internal_name')
        thumbnail1_vals = ('cat_thumb.jpg', 'XYXYXYXYXYXY')
        thumbnail2_vals = ('kitten_thumb.jpg', '123ABC123ABC')
        thumbnail3_vals = ('puppy_thumb.jpg', 'ADAM12ADAM12')
        thumbnail4_vals = ('meerkat_thumb.jpg', 'CHIPSPONCH14')
        thumbnail5_vals = ('corgi_thumb.jpg', 'RON8LDXFFFF10')

        thumbnail1 = dict(zip(thumbnail_fields[1:], thumbnail1_vals[1:]))
        thumbnail2 = dict(zip(thumbnail_fields[1:], thumbnail2_vals[1:]))
        thumbnail3 = dict(zip(thumbnail_fields[1:], thumbnail3_vals[1:]))
        thumbnail4 = dict(zip(thumbnail_fields[1:], thumbnail4_vals[1:]))
        non_existent_thumbnail = dict(zip(thumbnail_fields[1:], thumbnail5_vals[1:]))

        # Asset6 and thumbnail6 have equivalent information on purpose.
        thumbnail6_vals = ('asset.txt', 'JJJCCC747858')
        thumbnail6 = dict(zip(thumbnail_fields[1:], thumbnail6_vals[1:]))

        thumb1_key = course1_key.make_asset_key('thumbnail', thumbnail1_vals[0])
        thumb2_key = course1_key.make_asset_key('thumbnail', thumbnail2_vals[0])
        thumb3_key = course2_key.make_asset_key('thumbnail', thumbnail3_vals[0])
        thumb4_key = course2_key.make_asset_key('thumbnail', thumbnail4_vals[0])
        thumb5_key = course2_key.make_asset_key('thumbnail', thumbnail5_vals[0])
        thumb6_key = course2_key.make_asset_key('thumbnail', thumbnail6_vals[0])

        thumb1_md = AssetThumbnailMetadata(thumb1_key, **thumbnail1)
        thumb2_md = AssetThumbnailMetadata(thumb2_key, **thumbnail2)
        thumb3_md = AssetThumbnailMetadata(thumb3_key, **thumbnail3)
        thumb4_md = AssetThumbnailMetadata(thumb4_key, **thumbnail4)
        thumb5_md = AssetThumbnailMetadata(thumb5_key, **non_existent_thumbnail)
        thumb6_md = AssetThumbnailMetadata(thumb6_key, **thumbnail6)

        if store is not None:
            store.save_asset_thumbnail_metadata(course1_key, thumb1_md, ModuleStoreEnum.UserID.test)
            store.save_asset_thumbnail_metadata(course1_key, thumb2_md, ModuleStoreEnum.UserID.test)
            store.save_asset_thumbnail_metadata(course2_key, thumb3_md, ModuleStoreEnum.UserID.test)
            store.save_asset_thumbnail_metadata(course2_key, thumb4_md, ModuleStoreEnum.UserID.test)
            # thumb5 and thumb6 are not saved on purpose!

        return (thumb1_md, thumb2_md, thumb3_md, thumb4_md, thumb5_md, thumb6_md)

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

    def test_get_all_assets_with_paging(self):
        pass

    def test_copy_all_assets(self):
        pass
