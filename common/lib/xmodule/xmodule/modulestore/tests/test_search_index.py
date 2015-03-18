"""
Unit tests for search indexers
"""
from lazy.lazy import lazy
import os
import mock
import json

from uuid import uuid4
from datetime import datetime
from unittest import TestCase

from opaque_keys.edx.locator import CourseLocator, LibraryLocator, BlockUsageLocator, LibraryUsageLocator

from xmodule.modulestore import ModuleStoreWriteBase
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.search_index import get_indexer_for_location, CoursewareSearchIndexer, LibrarySearchIndexer


class TestIndexerForLocation(TestCase):
    """ Tests for search indexers factory method """
    def test_given_course_locator_returns_courseware_indexer(self):
        locator = mock.Mock(spec=CourseLocator)
        indexer = get_indexer_for_location(locator)
        self.assertIsInstance(indexer, CoursewareSearchIndexer)

    def test_given_library_locator_returns_library_indexer(self):
        locator = mock.Mock(spec=LibraryLocator)
        indexer = get_indexer_for_location(locator)
        self.assertIsInstance(indexer, LibrarySearchIndexer)

    def test_given_course_item_locator_returns_courseware_indexer(self):
        locator = mock.Mock(spec=BlockUsageLocator)
        locator.course_key = mock.Mock(spec=CourseLocator)
        indexer = get_indexer_for_location(locator)
        self.assertIsInstance(indexer, CoursewareSearchIndexer)

    def test_given_library_item_locator_returns_library_indexer(self):
        locator = mock.Mock(spec=LibraryUsageLocator)
        locator.course_key = mock.Mock(spec=LibraryLocator)
        indexer = get_indexer_for_location(locator)
        self.assertIsInstance(indexer, LibrarySearchIndexer)


class SearchIndexerBaseTestMixin(object):
    """ COmmon features for search indexers tests"""
    ROOT_ID = None
    TEST_INDEX_FILENAME = "test_root/index_file.dat"
    modulestore = None

    def setUp(self):
        """
        SetUp method. Sincerely yours, CO.
        Setting up mock search indexer backing file as prescribed by MOCK_SEARCH_BACKING_FILE setting
        """
        super(SearchIndexerBaseTestMixin, self).setUp()
        # this test implicitly uses MockSearchEngine, which in turn uses settings.MOCK_SEARCH_BACKING_FILE
        # as backing file - so we create it
        with open(self.TEST_INDEX_FILENAME, "w+") as index_file:
            json.dump({}, index_file)

        self.modulestore = mock.Mock(spec=ModuleStoreWriteBase)

    def tearDown(self):
        """
        TearDown method. Sincerely yours, CO.
        Removing backing file created in set up
        """
        super(SearchIndexerBaseTestMixin, self).tearDown()
        os.remove(self.TEST_INDEX_FILENAME)

    def _make_location(self, block_type, course_id=ROOT_ID):
        """ Builds xblock location for specified block type and course id """
        raise NotImplemented()

    def _process_index_id(self, location):
        """ Transforms block location to build correct index id """
        raise NotImplemented()

    @lazy
    def indexer(self):
        """ Indexer under test instantiation """
        raise NotImplemented()

    def _make_item(self, block_type, index_dictionary, course_id=None, start=None, children=None):
        """ Builds XBlock mock with specified block_type, index disctionary, children, etc."""
        location = self._make_location(block_type, course_id)
        result = mock.Mock()
        if index_dictionary is not None:
            result.index_dictionary = mock.Mock(return_value=index_dictionary)
        else:
            del result.index_dictionary
        result.start = start

        result.children = children if children else []
        result.has_children = len(result.children) > 0
        result.location = location
        result.scope_ids = mock.Mock()
        result.scope_ids.usage_id = location
        return result, location

    def _set_up_modulestore_get_item(self, items):
        """
        Sets up mock modulestore get_item method to return only items listed in `items` parameter at specified locations
        """
        def side_effect(loc, **kwargs):
            return items.get(loc, None)
        self.modulestore.get_item = mock.Mock(side_effect=side_effect)

    def _make_index_entry(self, index_dict, location, start_date=None):
        """ Helper method: builds index entry dictionary """
        result = {
            'id': self._process_index_id(location),
            'course': unicode(self.ROOT_ID),
        }
        result.update(index_dict)
        if start_date:
            result['start_date'] = start_date
        return result

    @mock.patch('search.tests.mock_search_engine.MockSearchEngine.remove')
    @mock.patch('search.tests.mock_search_engine.MockSearchEngine.index')
    @mock.patch('xmodule.modulestore.search_index.SearchEngine.get_search_engine')
    def test_no_searcher_does_nothing(self, search_engine, index, remove):
        """ Tests that does indexer does nothing if no search engine is available """
        search_engine.return_value = None
        item, location = self._make_item('html', {'item': 'value'})
        self.indexer.add_to_search_index(self.modulestore, location)
        search_engine.assert_called_with(self.indexer.INDEX_NAME)
        index.assert_not_called()
        remove.assert_not_called()

    @mock.patch('search.tests.mock_search_engine.MockSearchEngine.remove')
    @mock.patch('search.tests.mock_search_engine.MockSearchEngine.index')
    def test_not_indexable_no_children_does_nothing(self, index, remove):
        """ Tests that does indexer does nothing if xblock is not indexable """
        item, location = self._make_item('html', None)
        self._set_up_modulestore_get_item({location: item})
        self.indexer.add_to_search_index(self.modulestore, location)
        index.assert_not_called()
        remove.assert_not_called()

    @mock.patch('search.tests.mock_search_engine.MockSearchEngine.index')
    def test_add_to_index_no_children_adds_to_index(self, patched_index):
        """ Tests that indexer adds XBlock with no children to index """
        index_dict = {'item': 'value'}
        item, location = self._make_item('html', index_dict)
        self._set_up_modulestore_get_item({location: item})
        self.indexer.add_to_search_index(self.modulestore, location)
        expected_index_entry = self._make_index_entry(index_dict, location)
        patched_index.assert_called_with(self.indexer.DOCUMENT_TYPE, expected_index_entry)

    @mock.patch('search.tests.mock_search_engine.MockSearchEngine.remove')
    def test_add_to_index_with_delete_no_children_simple_removes_from_index(self, patched_remove):
        """ Tests that indexer removes XBlock with no children from index """
        item, location = self._make_item('html', {'item': 'value'})
        self._set_up_modulestore_get_item({location: item})
        self.indexer.add_to_search_index(self.modulestore, location, delete=True)
        patched_remove.assert_called_with(self.indexer.DOCUMENT_TYPE, self._process_index_id(location))

    @mock.patch('search.tests.mock_search_engine.MockSearchEngine.index')
    def test_add_to_index_with_chidlren_adds_all_to_index(self, patched_index):
        """ Tests that indexer adds XBlock with children to index (both Xblock and all of its children)"""
        index_dict_child1, index_dict_child2 = {'child': 'child1'}, {'child': 'child2'}
        child1, child_loc1 = self._make_item('text', index_dict_child1)
        child2, child_loc2 = self._make_item('html', index_dict_child2)

        index_dict = {'item': 'value'}
        start_date = datetime(2015, 7, 14, 22, 11, 03)

        item, location = self._make_item(
            'problem', index_dict,
            children=[child_loc1, child_loc2],
            start=start_date
        )
        self._set_up_modulestore_get_item({location: item, child_loc1: child1, child_loc2: child2})
        self.indexer.add_to_search_index(self.modulestore, location)

        calls = patched_index.call_args_list
        args, kwargs = calls[0]
        self.assertEqual(args, (
            self.indexer.DOCUMENT_TYPE,
            self._make_index_entry(index_dict_child1, child_loc1, start_date=start_date)
        ))
        args, kwargs = calls[1]
        self.assertEqual(args, (
            self.indexer.DOCUMENT_TYPE,
            self._make_index_entry(index_dict_child2, child_loc2, start_date=start_date)
        ))
        args, kwargs = calls[2]
        self.assertEqual(args, (
            self.indexer.DOCUMENT_TYPE,
            self._make_index_entry(index_dict, location, start_date=start_date)
        ))

    @mock.patch('search.tests.mock_search_engine.MockSearchEngine.remove')
    def test_add_to_index_with_chidlren_adds_all_to_index(self, patched_remove):
        """ Tests that indexer removes XBlock with children from index (both Xblock and all of its children)"""
        index_dict_child1, index_dict_child2 = {'child': 'child1'}, {'child': 'child2'}
        child1, child_loc1 = self._make_item('text', index_dict_child1)
        child2, child_loc2 = self._make_item('html', index_dict_child2)

        index_dict = {'item': 'value'}

        item, location = self._make_item('problem', index_dict, children=[child_loc1, child_loc2])
        self._set_up_modulestore_get_item({location: item, child_loc1: child1, child_loc2: child2})
        self.indexer.add_to_search_index(self.modulestore, location, delete=True)

        calls = patched_remove.call_args_list
        args, kwargs = calls[0]
        self.assertEqual(args, (self.indexer.DOCUMENT_TYPE, self._process_index_id(child_loc1)))
        args, kwargs = calls[1]
        self.assertEqual(args, (self.indexer.DOCUMENT_TYPE, self._process_index_id(child_loc2)))
        args, kwargs = calls[2]
        self.assertEqual(args, (self.indexer.DOCUMENT_TYPE, self._process_index_id(location)))


class TestCoursewareSearchIndexer(SearchIndexerBaseTestMixin, TestCase):
    """ Tests for CoursewareSearchIndexer """
    ROOT_ID = CourseLocator('testx', 'courseware_indexer_test', 'test_run')

    @lazy
    def indexer(self):
        """ Indexer under test instantiation """
        return CoursewareSearchIndexer()

    def _make_location(self, block_type, course_id=None):
        """ Builds xblock location for specified block type and course id """
        course_id = course_id if course_id else self.ROOT_ID
        return BlockUsageLocator(course_id, block_type, uuid4().hex)

    def _process_index_id(self, location):
        """ Transforms block location to build correct index id """
        return unicode(location)

    def _make_index_entry(self, index_dict, location, start_date=None):
        """ Helper method: builds index entry dictionary """
        result = {
            'id': self._process_index_id(location),
            'course': unicode(self.ROOT_ID),
        }
        result.update(index_dict)
        if start_date:
            result['start_date'] = start_date
        return result


class TestLibrarySearchIndexer(SearchIndexerBaseTestMixin, TestCase):
    """ Tests for LibrarySearchIndexer """
    ROOT_ID = LibraryLocator('lib', 'Lib1')

    @lazy
    def indexer(self):
        """ Indexer under test instantiation """
        return LibrarySearchIndexer()

    def _make_location(self, block_type, course_id=None):
        """ Builds xblock location for specified block type and course id """
        course_id = course_id if course_id else self.ROOT_ID
        return LibraryUsageLocator(course_id, block_type, uuid4().hex)

    def _process_index_id(self, location):
        """ Transforms block location to build correct index id """
        new_loc = location.replace(library_key=location.library_key.replace(version_guid=None, branch=None))
        return unicode(new_loc)

    def _make_index_entry(self, index_dict, location, start_date=None):
        """ Helper method: builds index entry dictionary """
        result = {
            'id': self._process_index_id(location),
            'library': unicode(self.ROOT_ID),
        }
        result.update(index_dict)
        if start_date:
            result['start_date'] = start_date
        return result
