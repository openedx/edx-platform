"""
Unittests for reindex_content_library management command
"""

from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings
from opaque_keys.edx.locator import LibraryLocatorV2, LibraryUsageLocatorV2
from search.search_engine_base import SearchEngine

from openedx.core.djangoapps.content_libraries.api import _lookup_usage_key
from openedx.core.djangoapps.content_libraries.constants import DRAFT_NAME
from openedx.core.djangoapps.content_libraries.libraries_index import ContentLibraryIndexer, LibraryBlockIndexer
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest, elasticsearch_test
from openedx.core.lib.blockstore_api import (
    get_or_create_bundle_draft,
    write_draft_file,
)


@override_settings(FEATURES={**settings.FEATURES, 'ENABLE_CONTENT_LIBRARY_INDEX': True})
@elasticsearch_test
class TestReindex(ContentLibrariesRestApiTest):
    """
    Tests for the reindex_content_library command
    """
    @elasticsearch_test
    def setUp(self, *args, **kwargs):
        super().setUp()
        ContentLibraryIndexer.remove_all_items()
        LibraryBlockIndexer.remove_all_items()
        self.searcher = SearchEngine.get_search_engine(ContentLibraryIndexer.INDEX_NAME)

        self.lib1 = self._create_library(slug="{}-1".format(self._testMethodName), title="Title 1")['id']
        self.lib2 = self._create_library(slug="{}-2".format(self._testMethodName), title="Title 2")['id']
        self.lib3 = self._create_library(slug="{}-3".format(self._testMethodName), title="Title 3")['id']

        self.block1 = self._add_block_to_library(self.lib1, "problem", "problem1")['id']
        self.block2 = self._add_block_to_library(self.lib1, "problem", "problem2")['id']
        self.block3 = self._add_block_to_library(self.lib2, "problem", "problem3")['id']

    def test_clear_all(self):
        """
        Test that --clear-all option removes all indexes
        """
        self.assertNotEqual(len(LibraryBlockIndexer.get_items(filter_terms={})), 0)
        self.assertNotEqual(len(ContentLibraryIndexer.get_items(filter_terms={})), 0)
        call_command("reindex_content_library", clear_all=True, force=True)
        self.assertEqual(len(ContentLibraryIndexer.get_items(filter_terms={})), 0)
        self.assertEqual(len(LibraryBlockIndexer.get_items(filter_terms={})), 0)

    def test_specific_items(self):
        """
        Test that specifying libraries to index doesn't index any other libraries/blocks
        """
        call_command("reindex_content_library", clear_all=True, force=True)
        call_command("reindex_content_library", self.lib1, force=True)
        self.assertEqual(len(ContentLibraryIndexer.get_items([self.lib1, self.lib2, self.lib3])), 1)
        self.assertEqual(len(LibraryBlockIndexer.get_items([self.block1, self.block2, self.block3])), 2)

    def test_all_items(self):
        """
        Test that --all indexes all libraries and blocks
        """
        call_command("reindex_content_library", clear_all=True, force=True)
        call_command("reindex_content_library", all=True, force=True)
        self.assertEqual(len(ContentLibraryIndexer.get_items([self.lib1, self.lib2, self.lib3])), 3)
        self.assertEqual(len(LibraryBlockIndexer.get_items([self.block1, self.block2, self.block3])), 3)

    def test_stale_removal(self):
        """
        Test that reindexing also removes stale indexes whose sources no longer exist
        """
        library_key_1 = LibraryLocatorV2.from_string(self.lib1)
        library_1 = ContentLibrary.objects.get_by_key(library_key_1)
        library_key_2 = LibraryLocatorV2.from_string(self.lib2)
        library_2 = ContentLibrary.objects.get_by_key(library_key_2)

        self.assertEqual(len(ContentLibraryIndexer.get_items([self.lib1, self.lib2, self.lib3])), 3)
        self.assertEqual(len(LibraryBlockIndexer.get_items([self.block1, self.block2, self.block3])), 3)

        # Delete a block without triggering index removal
        def_key, lib_bundle = _lookup_usage_key(LibraryUsageLocatorV2.from_string(self.block1))
        draft_uuid = get_or_create_bundle_draft(def_key.bundle_uuid, DRAFT_NAME).uuid
        write_draft_file(draft_uuid, 'problem/problem1/definition.xml', contents=None)
        lib_bundle.cache.clear()

        # Reindex library 1
        call_command("reindex_content_library", self.lib1, force=True)
        # Verify that stale block index got removed
        self.assertEqual(len(ContentLibraryIndexer.get_items([self.lib1, self.lib2, self.lib3])), 3)
        self.assertEqual(len(LibraryBlockIndexer.get_items([self.block1, self.block2, self.block3])), 2)

        library_1.delete()
        # Reindexing with --all causes stale library indexes to be removed
        call_command("reindex_content_library", all=True, force=True)
        self.assertEqual(len(ContentLibraryIndexer.get_items([self.lib1, self.lib2, self.lib3])), 2)
        self.assertEqual(len(LibraryBlockIndexer.get_items([self.block1, self.block2, self.block3])), 1)

        library_2.delete()
        # Reindexing specific libs doesn't remove stale library indexes
        call_command("reindex_content_library", self.lib3, force=True)
        self.assertEqual(len(ContentLibraryIndexer.get_items([self.lib1, self.lib2, self.lib3])), 2)
        self.assertEqual(len(LibraryBlockIndexer.get_items([self.block1, self.block2, self.block3])), 1)
