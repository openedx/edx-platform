"""
Unit tests for the Mongo modulestore
"""
# pylint: disable=protected-access
# pylint: disable=no-name-in-module
# pylint: disable=bad-continuation
from nose.tools import assert_equals, assert_raises, \
    assert_not_equals, assert_false, assert_true, assert_greater, assert_is_instance, assert_is_none
# pylint: enable=E0611
from path import Path as path
import pymongo
import logging
import shutil
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pytz import UTC
import unittest
from mock import patch
from xblock.core import XBlock

from xblock.fields import Scope, Reference, ReferenceList, ReferenceValueDict
from xblock.runtime import KeyValueStore
from xblock.exceptions import InvalidScopeError

from xmodule.tests import DATA_DIR
from opaque_keys.edx.locations import Location
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.mongo import MongoKeyValueStore
from xmodule.modulestore.draft import DraftModuleStore
from opaque_keys.edx.locations import SlashSeparatedCourseKey, AssetLocation
from opaque_keys.edx.locator import LibraryLocator, CourseLocator
from opaque_keys.edx.keys import UsageKey
from xmodule.modulestore.xml_exporter import export_course_to_xml
from xmodule.modulestore.xml_importer import import_course_from_xml, perform_xlint
from xmodule.contentstore.mongo import MongoContentStore

from nose.tools import assert_in
from xmodule.exceptions import NotFoundError
from git.test.lib.asserts import assert_not_none
from xmodule.x_module import XModuleMixin
from xmodule.modulestore.mongo.base import as_draft
from xmodule.modulestore.tests.mongo_connection import MONGO_PORT_NUM, MONGO_HOST
from xmodule.modulestore.tests.utils import LocationMixin, mock_tab_from_json
from xmodule.modulestore.edit_info import EditInfoMixin
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.inheritance import InheritanceMixin


log = logging.getLogger(__name__)

HOST = MONGO_HOST
PORT = MONGO_PORT_NUM
DB = 'test_mongo_%s' % uuid4().hex[:5]
COLLECTION = 'modulestore'
ASSET_COLLECTION = 'assetstore'
FS_ROOT = DATA_DIR  # TODO (vshnayder): will need a real fs_root for testing load_item
DEFAULT_CLASS = 'xmodule.raw_module.RawDescriptor'
RENDER_TEMPLATE = lambda t_n, d, ctx=None, nsp='main': ''


class ReferenceTestXBlock(XModuleMixin):
    """
    Test xblock type to test the reference field types
    """
    has_children = True
    reference_link = Reference(default=None, scope=Scope.content)
    reference_list = ReferenceList(scope=Scope.content)
    reference_dict = ReferenceValueDict(scope=Scope.settings)


class TestMongoModuleStoreBase(unittest.TestCase):
    '''
    Basic setup for all tests
    '''
    # Explicitly list the courses to load (don't want the big one)
    courses = ['toy', 'simple', 'simple_with_draft', 'test_unicode']

    @classmethod
    def setupClass(cls):
        cls.connection = pymongo.MongoClient(
            host=HOST,
            port=PORT,
            tz_aware=True,
            document_class=dict,
        )

        # NOTE: Creating a single db for all the tests to save time.  This
        # is ok only as long as none of the tests modify the db.
        # If (when!) that changes, need to either reload the db, or load
        # once and copy over to a tmp db for each test.
        cls.content_store, cls.draft_store = cls.initdb()

    @classmethod
    def teardownClass(cls):
        if cls.connection:
            cls.connection.drop_database(DB)
            cls.connection.close()

    @classmethod
    def add_asset_collection(cls, doc_store_config):
        """
        No asset collection.
        """
        pass

    @classmethod
    def initdb(cls):
        # connect to the db
        doc_store_config = {
            'host': HOST,
            'port': PORT,
            'db': DB,
            'collection': COLLECTION,
        }
        cls.add_asset_collection(doc_store_config)

        # since MongoModuleStore and MongoContentStore are basically assumed to be together, create this class
        # as well
        content_store = MongoContentStore(HOST, DB, port=PORT)
        #
        # Also test draft store imports
        #
        draft_store = DraftModuleStore(
            content_store,
            doc_store_config, FS_ROOT, RENDER_TEMPLATE,
            default_class=DEFAULT_CLASS,
            branch_setting_func=lambda: ModuleStoreEnum.Branch.draft_preferred,
            xblock_mixins=(EditInfoMixin, InheritanceMixin, LocationMixin, XModuleMixin)

        )

        with patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json):
            import_course_from_xml(
                draft_store,
                999,
                DATA_DIR,
                cls.courses,
                static_content_store=content_store
            )

            # also test a course with no importing of static content
            import_course_from_xml(
                draft_store,
                999,
                DATA_DIR,
                ['test_import_course'],
                static_content_store=content_store,
                do_import_static=False,
                verbose=True
            )

            # also import a course under a different course_id (especially ORG)
            import_course_from_xml(
                draft_store,
                999,
                DATA_DIR,
                ['test_import_course'],
                static_content_store=content_store,
                do_import_static=False,
                verbose=True,
                target_id=SlashSeparatedCourseKey('guestx', 'foo', 'bar')
            )

        return content_store, draft_store

    @staticmethod
    def destroy_db(connection):
        # Destroy the test db.
        connection.drop_database(DB)

    def setUp(self):
        super(TestMongoModuleStoreBase, self).setUp()
        self.dummy_user = ModuleStoreEnum.UserID.test


class TestMongoModuleStore(TestMongoModuleStoreBase):
    '''Module store tests'''

    @classmethod
    def add_asset_collection(cls, doc_store_config):
        """
        No asset collection - it's not used in the tests below.
        """
        pass

    @classmethod
    def setupClass(cls):
        super(TestMongoModuleStore, cls).setupClass()

    @classmethod
    def teardownClass(cls):
        super(TestMongoModuleStore, cls).teardownClass()

    def test_init(self):
        '''Make sure the db loads'''
        ids = list(self.connection[DB][COLLECTION].find({}, {'_id': True}))
        assert_greater(len(ids), 12)

    def test_mongo_modulestore_type(self):
        store = DraftModuleStore(
            None,
            {'host': HOST, 'db': DB, 'port': PORT, 'collection': COLLECTION},
            FS_ROOT, RENDER_TEMPLATE, default_class=DEFAULT_CLASS
        )
        assert_equals(store.get_modulestore_type(''), ModuleStoreEnum.Type.mongo)

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_get_courses(self, _from_json):
        '''Make sure the course objects loaded properly'''
        courses = self.draft_store.get_courses()

        assert_equals(len(courses), 6)
        course_ids = [course.id for course in courses]

        for course_key in [

            SlashSeparatedCourseKey(*fields)
            for fields in [
                ['edX', 'simple', '2012_Fall'],
                ['edX', 'simple_with_draft', '2012_Fall'],
                ['edX', 'test_import_course', '2012_Fall'],
                ['edX', 'test_unicode', '2012_Fall'],
                ['edX', 'toy', '2012_Fall'],
                ['guestx', 'foo', 'bar'],
            ]
        ]:
            assert_in(course_key, course_ids)
            course = self.draft_store.get_course(course_key)
            assert_not_none(course)
            assert_true(self.draft_store.has_course(course_key))
            mix_cased = SlashSeparatedCourseKey(
                course_key.org.upper(), course_key.course.upper(), course_key.run.lower()
            )
            assert_false(self.draft_store.has_course(mix_cased))
            assert_true(self.draft_store.has_course(mix_cased, ignore_case=True))

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_get_org_courses(self, _from_json):
        """
        Make sure that we can query for a filtered list of courses for a given ORG
        """

        courses = self.draft_store.get_courses(org='guestx')
        assert_equals(len(courses), 1)
        course_ids = [course.id for course in courses]

        for course_key in [
            SlashSeparatedCourseKey(*fields)
            for fields in [
                ['guestx', 'foo', 'bar']
            ]
        ]:
            assert_in(course_key, course_ids)

        courses = self.draft_store.get_courses(org='edX')
        assert_equals(len(courses), 5)
        course_ids = [course.id for course in courses]

        for course_key in [
            SlashSeparatedCourseKey(*fields)
            for fields in [
                ['edX', 'simple', '2012_Fall'],
                ['edX', 'simple_with_draft', '2012_Fall'],
                ['edX', 'test_import_course', '2012_Fall'],
                ['edX', 'test_unicode', '2012_Fall'],
                ['edX', 'toy', '2012_Fall'],
            ]
        ]:
            assert_in(course_key, course_ids)

    def test_no_such_course(self):
        """
        Test get_course and has_course with ids which don't exist
        """
        for course_key in [

            SlashSeparatedCourseKey(*fields)
            for fields in [
                ['edX', 'simple', 'no_such_course'], ['edX', 'no_such_course', '2012_Fall'],
                ['NO_SUCH_COURSE', 'Test_iMport_courSe', '2012_Fall'],
            ]
        ]:
            course = self.draft_store.get_course(course_key)
            assert_is_none(course)
            assert_false(self.draft_store.has_course(course_key))
            mix_cased = SlashSeparatedCourseKey(
                course_key.org.lower(), course_key.course.upper(), course_key.run.upper()
            )
            assert_false(self.draft_store.has_course(mix_cased))
            assert_false(self.draft_store.has_course(mix_cased, ignore_case=True))

    def test_has_course_with_library(self):
        """
        Test that has_course() returns False when called with a LibraryLocator.
        This is required because MixedModuleStore will use has_course() to check
        where a given library are stored.
        """
        lib_key = LibraryLocator("TestOrg", "TestLib")
        result = self.draft_store.has_course(lib_key)
        assert_false(result)

    def test_loads(self):
        assert_not_none(
            self.draft_store.get_item(Location('edX', 'toy', '2012_Fall', 'course', '2012_Fall'))
        )

        assert_not_none(
            self.draft_store.get_item(Location('edX', 'simple', '2012_Fall', 'course', '2012_Fall')),
        )

        assert_not_none(
            self.draft_store.get_item(Location('edX', 'toy', '2012_Fall', 'video', 'Welcome')),
        )

    def test_unicode_loads(self):
        """
        Test that getting items from the test_unicode course works
        """
        assert_not_none(
            self.draft_store.get_item(Location('edX', 'test_unicode', '2012_Fall', 'course', '2012_Fall')),
        )
        # All items with ascii-only filenames should load properly.
        assert_not_none(
            self.draft_store.get_item(Location('edX', 'test_unicode', '2012_Fall', 'video', 'Welcome')),
        )
        assert_not_none(
            self.draft_store.get_item(Location('edX', 'test_unicode', '2012_Fall', 'video', 'Welcome')),
        )
        assert_not_none(
            self.draft_store.get_item(Location('edX', 'test_unicode', '2012_Fall', 'chapter', 'Overview')),
        )

    def test_find_one(self):
        assert_not_none(
            self.draft_store._find_one(Location('edX', 'toy', '2012_Fall', 'course', '2012_Fall')),
        )

        assert_not_none(
            self.draft_store._find_one(Location('edX', 'simple', '2012_Fall', 'course', '2012_Fall')),
        )

        assert_not_none(
            self.draft_store._find_one(Location('edX', 'toy', '2012_Fall', 'video', 'Welcome')),
        )

    def test_xlinter(self):
        '''
        Run through the xlinter, we know the 'toy' course has violations, but the
        number will continue to grow over time, so just check > 0
        '''
        assert_not_equals(perform_xlint(DATA_DIR, ['toy']), 0)

    def test_get_courses_has_no_templates(self):
        courses = self.draft_store.get_courses()
        for course in courses:
            assert_false(
                course.location.org == 'edx' and course.location.course == 'templates',
                '{0} is a template course'.format(course)
            )

    def test_contentstore_attrs(self):
        """
        Test getting, setting, and defaulting the locked attr and arbitrary attrs.
        """
        location = Location('edX', 'toy', '2012_Fall', 'course', '2012_Fall')
        course_content, __ = self.content_store.get_all_content_for_course(location.course_key)
        assert_true(len(course_content) > 0)
        filter_params = _build_requested_filter('Images')
        filtered_course_content, __ = self.content_store.get_all_content_for_course(
            location.course_key, filter_params=filter_params)
        assert_true(len(filtered_course_content) < len(course_content))
        # a bit overkill, could just do for content[0]
        for content in course_content:
            assert not content.get('locked', False)
            asset_key = AssetLocation._from_deprecated_son(content.get('content_son', content['_id']), location.run)
            assert not self.content_store.get_attr(asset_key, 'locked', False)
            attrs = self.content_store.get_attrs(asset_key)
            assert_in('uploadDate', attrs)
            assert not attrs.get('locked', False)
            self.content_store.set_attr(asset_key, 'locked', True)
            assert self.content_store.get_attr(asset_key, 'locked', False)
            attrs = self.content_store.get_attrs(asset_key)
            assert_in('locked', attrs)
            assert attrs['locked'] is True
            self.content_store.set_attrs(asset_key, {'miscel': 99})
            assert_equals(self.content_store.get_attr(asset_key, 'miscel'), 99)

        asset_key = AssetLocation._from_deprecated_son(
            course_content[0].get('content_son', course_content[0]['_id']),
            location.run
        )
        assert_raises(
            AttributeError, self.content_store.set_attr, asset_key,
            'md5', 'ff1532598830e3feac91c2449eaa60d6'
        )
        assert_raises(
            AttributeError, self.content_store.set_attrs, asset_key,
            {'foo': 9, 'md5': 'ff1532598830e3feac91c2449eaa60d6'}
        )
        assert_raises(
            NotFoundError, self.content_store.get_attr,
            Location('bogus', 'bogus', 'bogus', 'asset', 'bogus'),
            'displayname'
        )
        assert_raises(
            NotFoundError, self.content_store.set_attr,
            Location('bogus', 'bogus', 'bogus', 'asset', 'bogus'),
            'displayname', 'hello'
        )
        assert_raises(
            NotFoundError, self.content_store.get_attrs,
            Location('bogus', 'bogus', 'bogus', 'asset', 'bogus')
        )
        assert_raises(
            NotFoundError, self.content_store.set_attrs,
            Location('bogus', 'bogus', 'bogus', 'asset', 'bogus'),
            {'displayname': 'hello'}
        )
        assert_raises(
            NotFoundError, self.content_store.set_attrs,
            Location('bogus', 'bogus', 'bogus', 'asset', None),
            {'displayname': 'hello'}
        )

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_get_courses_for_wiki(self, _from_json):
        """
        Test the get_courses_for_wiki method
        """
        for course_number in self.courses:
            course_locations = self.draft_store.get_courses_for_wiki(course_number)
            assert_equals(len(course_locations), 1)
            assert_equals(SlashSeparatedCourseKey('edX', course_number, '2012_Fall'), course_locations[0])

        course_locations = self.draft_store.get_courses_for_wiki('no_such_wiki')
        assert_equals(len(course_locations), 0)

        # set toy course to share the wiki with simple course
        toy_course = self.draft_store.get_course(SlashSeparatedCourseKey('edX', 'toy', '2012_Fall'))
        toy_course.wiki_slug = 'simple'
        self.draft_store.update_item(toy_course, ModuleStoreEnum.UserID.test)

        # now toy_course should not be retrievable with old wiki_slug
        course_locations = self.draft_store.get_courses_for_wiki('toy')
        assert_equals(len(course_locations), 0)

        # but there should be two courses with wiki_slug 'simple'
        course_locations = self.draft_store.get_courses_for_wiki('simple')
        assert_equals(len(course_locations), 2)
        for course_number in ['toy', 'simple']:
            assert_in(SlashSeparatedCourseKey('edX', course_number, '2012_Fall'), course_locations)

        # configure simple course to use unique wiki_slug.
        simple_course = self.draft_store.get_course(SlashSeparatedCourseKey('edX', 'simple', '2012_Fall'))
        simple_course.wiki_slug = 'edX.simple.2012_Fall'
        self.draft_store.update_item(simple_course, ModuleStoreEnum.UserID.test)
        # it should be retrievable with its new wiki_slug
        course_locations = self.draft_store.get_courses_for_wiki('edX.simple.2012_Fall')
        assert_equals(len(course_locations), 1)
        assert_in(SlashSeparatedCourseKey('edX', 'simple', '2012_Fall'), course_locations)

    @XBlock.register_temp_plugin(ReferenceTestXBlock, 'ref_test')
    def test_reference_converters(self):
        """
        Test that references types get deserialized correctly
        """
        course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

        def setup_test():
            course = self.draft_store.get_course(course_key)
            # can't use item factory as it depends on django settings
            p1ele = self.draft_store.create_item(
                99,
                course_key,
                'problem',
                block_id='p1',
                runtime=course.runtime
            )
            p2ele = self.draft_store.create_item(
                99,
                course_key,
                'problem',
                block_id='p2',
                runtime=course.runtime
            )
            self.refloc = course.id.make_usage_key('ref_test', 'ref_test')
            self.draft_store.create_item(
                99,
                self.refloc.course_key,
                self.refloc.block_type,
                block_id=self.refloc.block_id,
                runtime=course.runtime,
                fields={
                    'reference_link': p1ele.location,
                    'reference_list': [p1ele.location, p2ele.location],
                    'reference_dict': {'p1': p1ele.location, 'p2': p2ele.location},
                    'children': [p1ele.location, p2ele.location],
                }
            )

        def check_xblock_fields():
            def check_children(xblock):
                for child in xblock.children:
                    assert_is_instance(child, UsageKey)

            course = self.draft_store.get_course(course_key)
            check_children(course)

            refele = self.draft_store.get_item(self.refloc)
            check_children(refele)
            assert_is_instance(refele.reference_link, UsageKey)
            assert_greater(len(refele.reference_list), 0)
            for ref in refele.reference_list:
                assert_is_instance(ref, UsageKey)
            assert_greater(len(refele.reference_dict), 0)
            for ref in refele.reference_dict.itervalues():
                assert_is_instance(ref, UsageKey)

        def check_mongo_fields():
            def get_item(location):
                return self.draft_store._find_one(as_draft(location))

            def check_children(payload):
                for child in payload['definition']['children']:
                    assert_is_instance(child, basestring)

            refele = get_item(self.refloc)
            check_children(refele)
            assert_is_instance(refele['definition']['data']['reference_link'], basestring)
            assert_greater(len(refele['definition']['data']['reference_list']), 0)
            for ref in refele['definition']['data']['reference_list']:
                assert_is_instance(ref, basestring)
            assert_greater(len(refele['metadata']['reference_dict']), 0)
            for ref in refele['metadata']['reference_dict'].itervalues():
                assert_is_instance(ref, basestring)

        setup_test()
        check_xblock_fields()
        check_mongo_fields()

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_export_course_image(self, _from_json):
        """
        Test to make sure that we have a course image in the contentstore,
        then export it to ensure it gets copied to both file locations.
        """
        course_key = SlashSeparatedCourseKey('edX', 'simple', '2012_Fall')
        location = course_key.make_asset_key('asset', 'images_course_image.jpg')

        # This will raise if the course image is missing
        self.content_store.find(location)

        root_dir = path(mkdtemp())
        self.addCleanup(shutil.rmtree, root_dir)
        export_course_to_xml(self.draft_store, self.content_store, course_key, root_dir, 'test_export')
        self.assertTrue(path(root_dir / 'test_export/static/images/course_image.jpg').isfile())
        self.assertTrue(path(root_dir / 'test_export/static/images_course_image.jpg').isfile())

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_export_course_image_nondefault(self, _from_json):
        """
        Make sure that if a non-default image path is specified that we
        don't export it to the static default location
        """
        course = self.draft_store.get_course(SlashSeparatedCourseKey('edX', 'toy', '2012_Fall'))
        assert_true(course.course_image, 'just_a_test.jpg')

        root_dir = path(mkdtemp())
        self.addCleanup(shutil.rmtree, root_dir)
        export_course_to_xml(self.draft_store, self.content_store, course.id, root_dir, 'test_export')
        self.assertTrue(path(root_dir / 'test_export/static/just_a_test.jpg').isfile())
        self.assertFalse(path(root_dir / 'test_export/static/images/course_image.jpg').isfile())

    def test_course_without_image(self):
        """
        Make sure we elegantly passover our code when there isn't a static
        image
        """
        course = self.draft_store.get_course(SlashSeparatedCourseKey('edX', 'simple_with_draft', '2012_Fall'))
        root_dir = path(mkdtemp())
        self.addCleanup(shutil.rmtree, root_dir)
        export_course_to_xml(self.draft_store, self.content_store, course.id, root_dir, 'test_export')
        self.assertFalse(path(root_dir / 'test_export/static/images/course_image.jpg').isfile())
        self.assertFalse(path(root_dir / 'test_export/static/images_course_image.jpg').isfile())

    def _create_test_tree(self, name, user_id=None):
        """
        Creates and returns a tree with the following structure:
        Grandparent
            Parent Sibling
            Parent
                Child
                Child Sibling

        """
        if user_id is None:
            user_id = self.dummy_user

        org = 'edX'
        course = 'tree{}'.format(name)
        run = name

        if not self.draft_store.has_course(SlashSeparatedCourseKey(org, course, run)):
            self.draft_store.create_course(org, course, run, user_id)

            locations = {
                'grandparent': Location(org, course, run, 'chapter', 'grandparent'),
                'parent_sibling': Location(org, course, run, 'sequential', 'parent_sibling'),
                'parent': Location(org, course, run, 'sequential', 'parent'),
                'child_sibling': Location(org, course, run, 'vertical', 'child_sibling'),
                'child': Location(org, course, run, 'vertical', 'child'),
            }

            for key in locations:
                self.draft_store.create_item(
                    user_id,
                    locations[key].course_key,
                    locations[key].block_type,
                    block_id=locations[key].block_id
                )

            grandparent = self.draft_store.get_item(locations['grandparent'])
            grandparent.children += [locations['parent_sibling'], locations['parent']]
            self.draft_store.update_item(grandparent, user_id=user_id)

            parent = self.draft_store.get_item(locations['parent'])
            parent.children += [locations['child_sibling'], locations['child']]
            self.draft_store.update_item(parent, user_id=user_id)

            self.draft_store.publish(locations['parent'], user_id)
            self.draft_store.publish(locations['parent_sibling'], user_id)

        return locations

    def test_migrate_published_info(self):
        """
        Tests that blocks that were storing published_date and published_by through CMSBlockMixin are loaded correctly
        """

        # Insert the test block directly into the module store
        location = Location('edX', 'migration', '2012_Fall', 'html', 'test_html')
        published_date = datetime(1970, 1, 1, tzinfo=UTC)
        published_by = 123
        self.draft_store._update_single_item(
            as_draft(location),
            {
                'definition.data': {},
                'metadata': {
                    # published_date was previously stored as a list of time components, not a datetime
                    'published_date': list(published_date.timetuple()),
                    'published_by': published_by,
                },
            },
            allow_not_found=True,
        )

        # Retrieve the block and verify its fields
        component = self.draft_store.get_item(location)
        self.assertEqual(component.published_on, published_date)
        self.assertEqual(component.published_by, published_by)

    def test_draft_modulestore_create_child_with_position(self):
        """
        This test is designed to hit a specific set of use cases having to do with
        the child positioning logic found in mongo/base.py:create_child()
        """
        # Set up the draft module store
        course = self.draft_store.create_course("TestX", "ChildTest", "1234_A1", 1)
        first_child = self.draft_store.create_child(
            self.dummy_user,
            course.location,
            "chapter",
            block_id=course.location.block_id
        )
        second_child = self.draft_store.create_child(
            self.dummy_user,
            course.location,
            "chapter",
            block_id=course.location.block_id,
            position=0
        )

        # First child should have been moved to second position, and better child takes the lead
        course = self.draft_store.get_course(course.id)
        self.assertEqual(unicode(course.children[1]), unicode(first_child.location))
        self.assertEqual(unicode(course.children[0]), unicode(second_child.location))

        # Clean up the data so we don't break other tests which apparently expect a particular state
        self.draft_store.delete_course(course.id, self.dummy_user)

    def test_make_course_usage_key(self):
        """Test that we get back the appropriate usage key for the root of a course key."""
        course_key = CourseLocator(org="edX", course="101", run="2015")
        root_block_key = self.draft_store.make_course_usage_key(course_key)
        self.assertEqual(root_block_key.block_type, "course")
        self.assertEqual(root_block_key.name, "2015")


class TestMongoModuleStoreWithNoAssetCollection(TestMongoModuleStore):
    '''
    Tests a situation where no asset_collection is specified.
    '''

    @classmethod
    def add_asset_collection(cls, doc_store_config):
        """
        No asset collection.
        """
        pass

    @classmethod
    def setupClass(cls):
        super(TestMongoModuleStoreWithNoAssetCollection, cls).setupClass()

    @classmethod
    def teardownClass(cls):
        super(TestMongoModuleStoreWithNoAssetCollection, cls).teardownClass()

    def test_no_asset_collection(self):
        courses = self.draft_store.get_courses()
        course = courses[0]
        # Confirm that no specified asset collection name means empty asset metadata.
        self.assertEquals(self.draft_store.get_all_asset_metadata(course.id, 'asset'), [])

    def test_no_asset_invalid_key(self):
        course_key = CourseLocator(org="edx3", course="test_course", run=None, deprecated=True)
        # Confirm that invalid course key raises ItemNotFoundError
        self.assertRaises(ItemNotFoundError, lambda: self.draft_store.get_all_asset_metadata(course_key, 'asset')[:1])


class TestMongoKeyValueStore(unittest.TestCase):
    """
    Tests for MongoKeyValueStore.
    """

    def setUp(self):
        super(TestMongoKeyValueStore, self).setUp()
        self.data = {'foo': 'foo_value'}
        self.course_id = SlashSeparatedCourseKey('org', 'course', 'run')
        self.parent = self.course_id.make_usage_key('parent', 'p')
        self.children = [self.course_id.make_usage_key('child', 'a'), self.course_id.make_usage_key('child', 'b')]
        self.metadata = {'meta': 'meta_val'}
        self.kvs = MongoKeyValueStore(self.data, self.parent, self.children, self.metadata)

    def test_read(self):
        assert_equals(self.data['foo'], self.kvs.get(KeyValueStore.Key(Scope.content, None, None, 'foo')))
        assert_equals(self.parent, self.kvs.get(KeyValueStore.Key(Scope.parent, None, None, 'parent')))
        assert_equals(self.children, self.kvs.get(KeyValueStore.Key(Scope.children, None, None, 'children')))
        assert_equals(self.metadata['meta'], self.kvs.get(KeyValueStore.Key(Scope.settings, None, None, 'meta')))

    def test_read_invalid_scope(self):
        for scope in (Scope.preferences, Scope.user_info, Scope.user_state):
            key = KeyValueStore.Key(scope, None, None, 'foo')
            with assert_raises(InvalidScopeError):
                self.kvs.get(key)
            assert_false(self.kvs.has(key))

    def test_read_non_dict_data(self):
        self.kvs = MongoKeyValueStore('xml_data', self.parent, self.children, self.metadata)
        assert_equals('xml_data', self.kvs.get(KeyValueStore.Key(Scope.content, None, None, 'data')))

    def _check_write(self, key, value):
        self.kvs.set(key, value)
        assert_equals(value, self.kvs.get(key))

    def test_write(self):
        yield (self._check_write, KeyValueStore.Key(Scope.content, None, None, 'foo'), 'new_data')
        yield (self._check_write, KeyValueStore.Key(Scope.children, None, None, 'children'), [])
        yield (self._check_write, KeyValueStore.Key(Scope.children, None, None, 'parent'), None)
        yield (self._check_write, KeyValueStore.Key(Scope.settings, None, None, 'meta'), 'new_settings')

    def test_write_non_dict_data(self):
        self.kvs = MongoKeyValueStore('xml_data', self.parent, self.children, self.metadata)
        self._check_write(KeyValueStore.Key(Scope.content, None, None, 'data'), 'new_data')

    def test_write_invalid_scope(self):
        for scope in (Scope.preferences, Scope.user_info, Scope.user_state):
            with assert_raises(InvalidScopeError):
                self.kvs.set(KeyValueStore.Key(scope, None, None, 'foo'), 'new_value')

    def _check_delete_default(self, key, default_value):
        self.kvs.delete(key)
        assert_equals(default_value, self.kvs.get(key))
        assert self.kvs.has(key)

    def _check_delete_key_error(self, key):
        self.kvs.delete(key)
        with assert_raises(KeyError):
            self.kvs.get(key)
        assert_false(self.kvs.has(key))

    def test_delete(self):
        yield (self._check_delete_key_error, KeyValueStore.Key(Scope.content, None, None, 'foo'))
        yield (self._check_delete_default, KeyValueStore.Key(Scope.children, None, None, 'children'), [])
        yield (self._check_delete_key_error, KeyValueStore.Key(Scope.settings, None, None, 'meta'))

    def test_delete_invalid_scope(self):
        for scope in (Scope.preferences, Scope.user_info, Scope.user_state, Scope.parent):
            with assert_raises(InvalidScopeError):
                self.kvs.delete(KeyValueStore.Key(scope, None, None, 'foo'))


def _build_requested_filter(requested_filter):
    """
    Returns requested filter_params string.
    """

    # Files and Uploads type filter values
    all_filters = {
        "Images": ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/tiff', 'image/tif', 'image/x-icon'],
        "Documents": [
            'application/pdf',
            'text/plain',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.template',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.openxmlformats-officedocument.presentationml.slideshow',
            'application/vnd.openxmlformats-officedocument.presentationml.template',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
            'application/msword',
            'application/vnd.ms-excel',
            'application/vnd.ms-powerpoint',
        ],
    }
    requested_file_types = all_filters.get(requested_filter, None)
    where = ["JSON.stringify(this.contentType).toUpperCase() == JSON.stringify('{}').toUpperCase()".format(
        req_filter) for req_filter in requested_file_types]
    filter_params = {
        "$where": ' || '.join(where),
    }
    return filter_params
