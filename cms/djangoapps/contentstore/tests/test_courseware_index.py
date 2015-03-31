"""
Testing indexing of the courseware as it is changed
"""
import ddt
from datetime import datetime
from mock import patch
from pytz import UTC
from uuid import uuid4

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.edit_info import EditInfoMixin
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.mixed import MixedModuleStore
from xmodule.modulestore.tests.utils import MixedSplitTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.test_cross_modulestore_import_export import MongoContentstoreBuilder
from xmodule.modulestore.tests.utils import create_modulestore_instance, LocationMixin
from xmodule.modulestore.tests.mongo_connection import MONGO_PORT_NUM, MONGO_HOST
from xmodule.tests import DATA_DIR
from search.search_engine_base import SearchEngine

from contentstore.courseware_index import CoursewareSearchIndexer, INDEX_NAME, SearchIndexingError


@ddt.ddt
class TestCoursewareSearchIndexer(MixedSplitTestCase):
    """ Tests the operation of the CoursewareSearchIndexer """
    HOST = MONGO_HOST
    PORT = MONGO_PORT_NUM
    DATABASE = 'test_mongo_%s' % uuid4().hex[:5]
    COLLECTION = 'modulestore'
    ASSET_COLLECTION = 'assetstore'
    DEFAULT_CLASS = 'xmodule.raw_module.RawDescriptor'
    RENDER_TEMPLATE = lambda t_n, d, ctx=None, nsp='main': ''
    modulestore_options = {
        'default_class': DEFAULT_CLASS,
        'fs_root': DATA_DIR,
        'render_template': RENDER_TEMPLATE,
        'xblock_mixins': (EditInfoMixin, InheritanceMixin, LocationMixin),
    }
    DOC_STORE_CONFIG = {
        'host': HOST,
        'port': PORT,
        'db': DATABASE,
        'collection': COLLECTION,
        'asset_collection': ASSET_COLLECTION,
    }
    OPTIONS = {
        'stores': [
            {
                'NAME': 'draft',
                'ENGINE': 'xmodule.modulestore.mongo.draft.DraftModuleStore',
                'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                'OPTIONS': modulestore_options
            },
            {
                'NAME': 'split',
                'ENGINE': 'xmodule.modulestore.split_mongo.split_draft.DraftVersioningModuleStore',
                'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                'OPTIONS': modulestore_options
            },
            {
                'NAME': 'xml',
                'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
                'OPTIONS': {
                    'data_dir': DATA_DIR,
                    'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                    'xblock_mixins': modulestore_options['xblock_mixins'],
                }
            },
        ]
    }

    def setUp(self):
        super(TestCoursewareSearchIndexer, self).setUp()

        self.course = None
        self.chapter = None
        self.sequential = None
        self.vertical = None
        self.html_unit = None

    def setup_course_base(self, store):
        """
        Set up the for the course outline tests.
        """
        self.course = CourseFactory.create(modulestore=store, start=datetime(2015, 3, 1, tzinfo=UTC))

        self.chapter = ItemFactory.create(
            parent_location=self.course.location,
            category='chapter',
            display_name="Week 1",
            modulestore=store,
            publish_item=True,
            start=datetime(2015, 3, 1, tzinfo=UTC),
        )
        self.sequential = ItemFactory.create(
            parent_location=self.chapter.location,
            category='sequential',
            display_name="Lesson 1",
            modulestore=store,
            publish_item=True,
            start=datetime(2015, 3, 1, tzinfo=UTC),
        )
        self.vertical = ItemFactory.create(
            parent_location=self.sequential.location,
            category='vertical',
            display_name='Subsection 1',
            modulestore=store,
            publish_item=True,
            start=datetime(2015, 4, 1, tzinfo=UTC),
        )
        # unspecified start - should inherit from container
        self.html_unit = ItemFactory.create(
            parent_location=self.vertical.location,
            category="html",
            display_name="Html Content",
            modulestore=store,
            publish_item=False,
        )

    def reindex_course(self, store):
        """ kick off complete reindex of the course """
        return CoursewareSearchIndexer.do_course_reindex(store, self.course.id)

    def index_recent_changes(self, store, since_time):
        """ index course using recent changes """
        trigger_time = datetime.now(UTC)
        return CoursewareSearchIndexer.index_course(
            store,
            self.course.id,
            triggered_at=trigger_time,
            reindex_age=(trigger_time - since_time)
        )

    def publish_item(self, store, item_location):
        """ publish the item at the given location """
        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            store.publish(item_location, ModuleStoreEnum.UserID.test)

    def delete_item(self, store, item_location):
        """ delete the item at the given location """
        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            store.delete_item(item_location, ModuleStoreEnum.UserID.test)

    def update_item(self, store, item):
        """ update the item at the given location """
        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            store.update_item(item, ModuleStoreEnum.UserID.test)

    def get_search_engine(self):
        """ Cenralized call to getting the search engin for the test """
        return SearchEngine.get_search_engine(INDEX_NAME)

    def _perform_test_using_store(self, store_type, test_to_perform):
        """ Helper method to run a test function that uses a specific store """
        with MongoContentstoreBuilder().build() as contentstore:
            store = MixedModuleStore(
                contentstore=contentstore,
                create_modulestore_instance=create_modulestore_instance,
                mappings={},
                **self.OPTIONS
            )
            self.addCleanup(store.close_all_connections)

            with store.default_store(store_type):
                self.setup_course_base(store)
                test_to_perform(store)

    def _test_indexing_course(self, store):
        """ indexing course tests """
        searcher = self.get_search_engine()
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 0)

        # Only published modules should be in the index
        added_to_index = self.reindex_course(store)
        self.assertEqual(added_to_index, 3)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 3)

        # Publish the vertical as is, and any unpublished children should now be available
        self.publish_item(store, self.vertical.location)
        self.reindex_course(store)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 4)

    def _test_not_indexing_unpublished_content(self, store):
        """ add a new one, only appers in index once added """
        searcher = self.get_search_engine()
        # Publish the vertical to start with
        self.publish_item(store, self.vertical.location)
        self.reindex_course(store)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 4)

        # Now add a new unit to the existing vertical
        ItemFactory.create(
            parent_location=self.vertical.location,
            category="html",
            display_name="Some other content",
            publish_item=False,
            modulestore=store,
        )
        self.reindex_course(store)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 4)

        # Now publish it and we should find it
        # Publish the vertical as is, and everything should be available
        self.publish_item(store, self.vertical.location)
        self.reindex_course(store)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 5)

    def _test_deleting_item(self, store):
        """ test deleting an item """
        searcher = self.get_search_engine()
        # Publish the vertical to start with
        self.publish_item(store, self.vertical.location)
        self.reindex_course(store)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 4)

        # just a delete should not change anything
        self.delete_item(store, self.html_unit.location)
        self.reindex_course(store)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 4)

        # but after publishing, we should no longer find the html_unit
        self.publish_item(store, self.vertical.location)
        self.reindex_course(store)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 3)

    def _test_not_indexable(self, store):
        """ test not indexable items """
        searcher = self.get_search_engine()
        # Publish the vertical to start with
        self.publish_item(store, self.vertical.location)
        self.reindex_course(store)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 4)

        # Add a non-indexable item
        ItemFactory.create(
            parent_location=self.vertical.location,
            category="problem",
            display_name="Some other content",
            publish_item=False,
            modulestore=store,
        )
        self.reindex_course(store)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 4)

        # even after publishing, we should not find the non-indexable item
        self.publish_item(store, self.vertical.location)
        self.reindex_course(store)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 4)

    def _test_start_date_propagation(self, store):
        """ make sure that the start date is applied at the right level """
        searcher = self.get_search_engine()
        early_date = self.course.start
        later_date = self.vertical.start

        # Publish the vertical
        self.publish_item(store, self.vertical.location)
        self.reindex_course(store)
        response = searcher.search(field_dictionary={"course": unicode(self.course.id)})
        self.assertEqual(response["total"], 4)

        results = response["results"]
        date_map = {
            unicode(self.chapter.location): early_date,
            unicode(self.sequential.location): early_date,
            unicode(self.vertical.location): later_date,
            unicode(self.html_unit.location): later_date,
        }
        for result in results:
            self.assertEqual(result["data"]["start_date"], date_map[result["data"]["id"]])

    @patch('django.conf.settings.SEARCH_ENGINE', None)
    def _test_search_disabled(self, store):
        """ if search setting has it as off, confirm that nothing is indexed """
        indexed_count = self.reindex_course(store)
        self.assertFalse(indexed_count)

    def _test_time_based_index(self, store):
        """ Make sure that a time based request to index does not index anything too old """
        self.publish_item(store, self.vertical.location)
        indexed_count = self.reindex_course(store)
        self.assertEqual(indexed_count, 4)

        # Add a new sequential
        sequential2 = ItemFactory.create(
            parent_location=self.chapter.location,
            category='sequential',
            display_name='Section 2',
            modulestore=store,
            publish_item=True,
            start=datetime(2015, 3, 1, tzinfo=UTC),
        )

        # add a new vertical
        vertical2 = ItemFactory.create(
            parent_location=sequential2.location,
            category='vertical',
            display_name='Subsection 2',
            modulestore=store,
            publish_item=True,
        )
        ItemFactory.create(
            parent_location=vertical2.location,
            category="html",
            display_name="Some other content",
            publish_item=False,
            modulestore=store,
        )

        before_time = datetime.now(UTC)
        self.publish_item(store, vertical2.location)
        # index based on time, will include an index of the origin sequential
        # because it is in a common subtree but not of the original vertical
        # because the original sequential's subtree is too old
        new_indexed_count = self.index_recent_changes(store, before_time)
        self.assertEqual(new_indexed_count, 5)

        # full index again
        indexed_count = self.reindex_course(store)
        self.assertEqual(indexed_count, 7)

    @patch('django.conf.settings.SEARCH_ENGINE', 'search.tests.tests.ErroringIndexEngine')
    def _test_exception(self, store):
        """ Test that exception within indexing yields a SearchIndexingError """
        self.publish_item(store, self.vertical.location)
        with self.assertRaises(SearchIndexingError):
            self.reindex_course(store)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_indexing_course(self, store_type):
        self._perform_test_using_store(store_type, self._test_indexing_course)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_not_indexing_unpublished_content(self, store_type):
        self._perform_test_using_store(store_type, self._test_not_indexing_unpublished_content)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_deleting_item(self, store_type):
        self._perform_test_using_store(store_type, self._test_deleting_item)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_not_indexable(self, store_type):
        self._perform_test_using_store(store_type, self._test_not_indexable)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_start_date_propagation(self, store_type):
        self._perform_test_using_store(store_type, self._test_start_date_propagation)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_search_disabled(self, store_type):
        self._perform_test_using_store(store_type, self._test_search_disabled)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_time_based_index(self, store_type):
        self._perform_test_using_store(store_type, self._test_time_based_index)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_exception(self, store_type):
        self._perform_test_using_store(store_type, self._test_exception)
