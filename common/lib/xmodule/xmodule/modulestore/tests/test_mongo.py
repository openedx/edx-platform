from pprint import pprint
# pylint: disable=E0611
from nose.tools import assert_equals, assert_raises, \
    assert_not_equals, assert_false
from itertools import ifilter
# pylint: enable=E0611
import pymongo
import logging
from uuid import uuid4

from xblock.fields import Scope
from xblock.runtime import KeyValueStore
from xblock.exceptions import InvalidScopeError

from xmodule.tests import DATA_DIR
from xmodule.modulestore import Location, MONGO_MODULESTORE_TYPE
from xmodule.modulestore.mongo import MongoModuleStore, MongoKeyValueStore
from xmodule.modulestore.draft import DraftModuleStore
from xmodule.modulestore.xml_importer import import_from_xml, perform_xlint
from xmodule.contentstore.mongo import MongoContentStore

from xmodule.modulestore.tests.test_modulestore import check_path_to_location
from nose.tools import assert_in
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.exceptions import InsufficientSpecificationError

log = logging.getLogger(__name__)

HOST = 'localhost'
PORT = 27017
DB = 'test_mongo_%s' % uuid4().hex[:5]
COLLECTION = 'modulestore'
FS_ROOT = DATA_DIR  # TODO (vshnayder): will need a real fs_root for testing load_item
DEFAULT_CLASS = 'xmodule.raw_module.RawDescriptor'
RENDER_TEMPLATE = lambda t_n, d, ctx = None, nsp = 'main': ''


class TestMongoModuleStore(object):
    '''Tests!'''
    # Explicitly list the courses to load (don't want the big one)
    courses = ['toy', 'simple', 'simple_with_draft', 'test_unicode']

    @classmethod
    def setupClass(cls):
        cls.connection = pymongo.MongoClient(
            host=HOST,
            port=PORT,
            tz_aware=True,
        )
        cls.connection.drop_database(DB)

        # NOTE: Creating a single db for all the tests to save time.  This
        # is ok only as long as none of the tests modify the db.
        # If (when!) that changes, need to either reload the db, or load
        # once and copy over to a tmp db for each test.
        cls.store, cls.content_store, cls.draft_store = cls.initdb()

    @classmethod
    def teardownClass(cls):
        if cls.connection:
            cls.connection.drop_database(DB)
            cls.connection.close()

    @staticmethod
    def initdb():
        # connect to the db
        doc_store_config = {
            'host': HOST,
            'db': DB,
            'collection': COLLECTION,
        }
        store = MongoModuleStore(doc_store_config, FS_ROOT, RENDER_TEMPLATE, default_class=DEFAULT_CLASS)
        # since MongoModuleStore and MongoContentStore are basically assumed to be together, create this class
        # as well
        content_store = MongoContentStore(HOST, DB)
        #
        # Also test draft store imports
        #
        draft_store = DraftModuleStore(doc_store_config, FS_ROOT, RENDER_TEMPLATE, default_class=DEFAULT_CLASS)
        import_from_xml(store, DATA_DIR, TestMongoModuleStore.courses, draft_store=draft_store, static_content_store=content_store)

        # also test a course with no importing of static content
        import_from_xml(
            store,
            DATA_DIR,
            ['test_import_course'],
            static_content_store=content_store,
            do_import_static=False,
            verbose=True
        )

        return store, content_store, draft_store

    @staticmethod
    def destroy_db(connection):
        # Destroy the test db.
        connection.drop_database(DB)

    def setUp(self):
        # make a copy for convenience
        self.connection = TestMongoModuleStore.connection

    def tearDown(self):
        pass

    def get_course_by_id(self, name):
        """
        Returns the first course with `id` of `name`, or `None` if there are none.
        """
        courses = self.store.get_courses()
        return next(ifilter(lambda x: x.id == name, courses), None)

    def course_with_id_exists(self, name):
        """
        Returns true iff there exists some course with `id` of `name`.
        """
        return (self.get_course_by_id(name) is not None)

    def test_init(self):
        '''Make sure the db loads, and print all the locations in the db.
        Call this directly from failing tests to see what is loaded'''
        ids = list(self.connection[DB][COLLECTION].find({}, {'_id': True}))

        pprint([Location(i['_id']).url() for i in ids])

    def test_mongo_modulestore_type(self):
        store = MongoModuleStore(
            {'host': HOST, 'db': DB, 'collection': COLLECTION},
            FS_ROOT, RENDER_TEMPLATE, default_class=DEFAULT_CLASS
        )
        assert_equals(store.get_modulestore_type('foo/bar/baz'), MONGO_MODULESTORE_TYPE)

    def test_get_courses(self):
        '''Make sure the course objects loaded properly'''
        courses = self.store.get_courses()
        assert_equals(len(courses), 5)
        assert self.course_with_id_exists('edX/simple/2012_Fall')
        assert self.course_with_id_exists('edX/simple_with_draft/2012_Fall')
        assert self.course_with_id_exists('edX/test_import_course/2012_Fall')
        assert self.course_with_id_exists('edX/test_unicode/2012_Fall')
        assert self.course_with_id_exists('edX/toy/2012_Fall')

    def test_loads(self):
        assert_not_equals(
            self.store.get_item("i4x://edX/toy/course/2012_Fall"),
            None)

        assert_not_equals(
            self.store.get_item("i4x://edX/simple/course/2012_Fall"),
            None)

        assert_not_equals(
            self.store.get_item("i4x://edX/toy/video/Welcome"),
            None)

    def test_unicode_loads(self):
        assert_not_equals(
            self.store.get_item("i4x://edX/test_unicode/course/2012_Fall"),
            None)
        # All items with ascii-only filenames should load properly.
        assert_not_equals(
            self.store.get_item("i4x://edX/test_unicode/video/Welcome"),
            None)
        assert_not_equals(
            self.store.get_item("i4x://edX/test_unicode/video/Welcome"),
            None)
        assert_not_equals(
            self.store.get_item("i4x://edX/test_unicode/chapter/Overview"),
            None)


    def test_find_one(self):
        assert_not_equals(
            self.store._find_one(Location("i4x://edX/toy/course/2012_Fall")),
            None)

        assert_not_equals(
            self.store._find_one(Location("i4x://edX/simple/course/2012_Fall")),
            None)

        assert_not_equals(
            self.store._find_one(Location("i4x://edX/toy/video/Welcome")),
            None)

    def test_path_to_location(self):
        '''Make sure that path_to_location works'''
        check_path_to_location(self.store)

    def test_xlinter(self):
        '''
        Run through the xlinter, we know the 'toy' course has violations, but the
        number will continue to grow over time, so just check > 0
        '''
        assert_not_equals(perform_xlint(DATA_DIR, ['toy']), 0)

    def test_get_courses_has_no_templates(self):
        courses = self.store.get_courses()
        for course in courses:
            assert_false(
                course.location.org == 'edx' and course.location.course == 'templates',
                '{0} is a template course'.format(course)
            )

    def test_static_tab_names(self):

        def get_tab_name(index):
            """
            Helper function for pulling out the name of a given static tab.

            Assumes the information is desired for courses[4] ('toy' course).
            """
            course = self.get_course_by_id('edX/toy/2012_Fall')
            return course.tabs[index]['name']

        # There was a bug where model.save was not getting called after the static tab name
        # was set set for tabs that have a URL slug. 'Syllabus' and 'Resources' fall into that
        # category, but for completeness, I'm also testing 'Course Info' and 'Discussion' (no url slug).
        assert_equals('Course Info', get_tab_name(1))
        assert_equals('Syllabus', get_tab_name(2))
        assert_equals('Resources', get_tab_name(3))
        assert_equals('Discussion', get_tab_name(4))

    def test_contentstore_attrs(self):
        """
        Test getting, setting, and defaulting the locked attr and arbitrary attrs.
        """
        location = Location('i4x', 'edX', 'toy', 'course', '2012_Fall')
        course_content, __ = TestMongoModuleStore.content_store.get_all_content_for_course(location)
        assert len(course_content) > 0
        # a bit overkill, could just do for content[0]
        for content in course_content:
            assert not content.get('locked', False)
            assert not TestMongoModuleStore.content_store.get_attr(content['_id'], 'locked', False)
            attrs = TestMongoModuleStore.content_store.get_attrs(content['_id'])
            assert_in('uploadDate', attrs)
            assert not attrs.get('locked', False)
            TestMongoModuleStore.content_store.set_attr(content['_id'], 'locked', True)
            assert TestMongoModuleStore.content_store.get_attr(content['_id'], 'locked', False)
            attrs = TestMongoModuleStore.content_store.get_attrs(content['_id'])
            assert_in('locked', attrs)
            assert attrs['locked'] is True
            TestMongoModuleStore.content_store.set_attrs(content['_id'], {'miscel': 99})
            assert_equals(TestMongoModuleStore.content_store.get_attr(content['_id'], 'miscel'), 99)
        assert_raises(
            AttributeError, TestMongoModuleStore.content_store.set_attr, course_content[0]['_id'],
            'md5', 'ff1532598830e3feac91c2449eaa60d6'
        )
        assert_raises(
            AttributeError, TestMongoModuleStore.content_store.set_attrs, course_content[0]['_id'],
            {'foo': 9, 'md5': 'ff1532598830e3feac91c2449eaa60d6'}
        )
        assert_raises(
            NotFoundError, TestMongoModuleStore.content_store.get_attr,
            Location('bogus', 'bogus', 'bogus', 'asset', 'bogus'),
            'displayname'
        )
        assert_raises(
            NotFoundError, TestMongoModuleStore.content_store.set_attr,
            Location('bogus', 'bogus', 'bogus', 'asset', 'bogus'),
            'displayname', 'hello'
        )
        assert_raises(
            NotFoundError, TestMongoModuleStore.content_store.get_attrs,
            Location('bogus', 'bogus', 'bogus', 'asset', 'bogus')
        )
        assert_raises(
            NotFoundError, TestMongoModuleStore.content_store.set_attrs,
            Location('bogus', 'bogus', 'bogus', 'asset', 'bogus'),
            {'displayname': 'hello'}
        )
        assert_raises(
            InsufficientSpecificationError, TestMongoModuleStore.content_store.set_attrs,
            Location('bogus', 'bogus', 'bogus', 'asset', None),
            {'displayname': 'hello'}
        )

    def test_get_courses_for_wiki(self):
        """
        Test the get_courses_for_wiki method
        """
        for course_number in self.courses:
            course_locations = self.store.get_courses_for_wiki(course_number)
            assert_equals(len(course_locations), 1)
            assert_equals(Location('i4x', 'edX', course_number, 'course', '2012_Fall'), course_locations[0])

        course_locations = self.store.get_courses_for_wiki('no_such_wiki')
        assert_equals(len(course_locations), 0)

        # set toy course to share the wiki with simple course
        toy_course = self.store.get_course('edX/toy/2012_Fall')
        toy_course.wiki_slug = 'simple'
        self.store.update_item(toy_course)

        # now toy_course should not be retrievable with old wiki_slug
        course_locations = self.store.get_courses_for_wiki('toy')
        assert_equals(len(course_locations), 0)

        # but there should be two courses with wiki_slug 'simple'
        course_locations = self.store.get_courses_for_wiki('simple')
        assert_equals(len(course_locations), 2)
        for course_number in ['toy', 'simple']:
            assert_in(Location('i4x', 'edX', course_number, 'course', '2012_Fall'), course_locations)

        # configure simple course to use unique wiki_slug.
        simple_course = self.store.get_course('edX/simple/2012_Fall')
        simple_course.wiki_slug = 'edX.simple.2012_Fall'
        self.store.update_item(simple_course)
        # it should be retrievable with its new wiki_slug
        course_locations = self.store.get_courses_for_wiki('edX.simple.2012_Fall')
        assert_equals(len(course_locations), 1)
        assert_in(Location('i4x', 'edX', 'simple', 'course', '2012_Fall'), course_locations)


class TestMongoKeyValueStore(object):
    """
    Tests for MongoKeyValueStore.
    """

    def setUp(self):
        self.data = {'foo': 'foo_value'}
        self.location = Location('i4x://org/course/category/name@version')
        self.children = ['i4x://org/course/child/a', 'i4x://org/course/child/b']
        self.metadata = {'meta': 'meta_val'}
        self.kvs = MongoKeyValueStore(self.data, self.children, self.metadata)

    def test_read(self):
        assert_equals(self.data['foo'], self.kvs.get(KeyValueStore.Key(Scope.content, None, None, 'foo')))
        assert_equals(self.children, self.kvs.get(KeyValueStore.Key(Scope.children, None, None, 'children')))
        assert_equals(self.metadata['meta'], self.kvs.get(KeyValueStore.Key(Scope.settings, None, None, 'meta')))
        assert_equals(None, self.kvs.get(KeyValueStore.Key(Scope.parent, None, None, 'parent')))

    def test_read_invalid_scope(self):
        for scope in (Scope.preferences, Scope.user_info, Scope.user_state):
            key = KeyValueStore.Key(scope, None, None, 'foo')
            with assert_raises(InvalidScopeError):
                self.kvs.get(key)
            assert_false(self.kvs.has(key))

    def test_read_non_dict_data(self):
        self.kvs = MongoKeyValueStore('xml_data', self.children, self.metadata)
        assert_equals('xml_data', self.kvs.get(KeyValueStore.Key(Scope.content, None, None, 'data')))

    def _check_write(self, key, value):
        self.kvs.set(key, value)
        assert_equals(value, self.kvs.get(key))

    def test_write(self):
        yield (self._check_write, KeyValueStore.Key(Scope.content, None, None, 'foo'), 'new_data')
        yield (self._check_write, KeyValueStore.Key(Scope.children, None, None, 'children'), [])
        yield (self._check_write, KeyValueStore.Key(Scope.settings, None, None, 'meta'), 'new_settings')

    def test_write_non_dict_data(self):
        self.kvs = MongoKeyValueStore('xml_data', self.children, self.metadata)
        self._check_write(KeyValueStore.Key(Scope.content, None, None, 'data'), 'new_data')

    def test_write_invalid_scope(self):
        for scope in (Scope.preferences, Scope.user_info, Scope.user_state, Scope.parent):
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
